import json
from dataclasses import dataclass
from typing import Any

from django.apps import apps
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Max, Model
from django.db.models.query import QuerySet
from django.utils import timezone

from bloomerp.automation.actions.merge_branches import WaitForOtherBranchResult
from bloomerp.automation.flows.for_each import ForEachResult
from bloomerp.automation.flows.if_condition import BranchStopped
from bloomerp.automation.workflow_state import ScopeKey, WorkflowRunState
from bloomerp.celery.tasks.workflow_task import resume_workflow_async, run_workflow_async
from bloomerp.communication.inbox_sources import publish_event
from bloomerp.models.automation.workflow import Workflow
from bloomerp.models.automation.workflow_node import WorkflowNode
from bloomerp.models.automation.workflow_run import WorkflowRun
from bloomerp.models.automation.workflow_run_step import WorkflowRunStep, WorkflowRunStepStatus
from bloomerp.utils.json_serialization import make_json_safe


_NO_OUTPUT = object()


class _WorkflowPaused(Exception):
    pass


@dataclass(frozen=True)
class WorkflowExecutionFrame:
    node: WorkflowNode
    input_data: object
    from_node: WorkflowNode | None = None
    from_step: WorkflowRunStep | None = None
    scope_key: ScopeKey = ()


def _node_input_key(node: WorkflowNode) -> str:
    return f"node_{node.id}"

def _serialize_trigger_data(value):
    if isinstance(value, ForEachResult):
        return {
            "__workflow_value__": "for_each_result",
            "items": _serialize_trigger_data(value.items),
        }

    if isinstance(value, BranchStopped):
        return {
            "__workflow_value__": "branch_stopped",
            "reason": value.reason,
        }

    if isinstance(value, WaitForOtherBranchResult):
        return {
            "__workflow_value__": "wait_for_other_branch",
            "arrived_branch_ids": value.arrived_branch_ids,
            "waiting_for_branch_ids": value.waiting_for_branch_ids,
        }

    if isinstance(value, Model):
        return {
            "__model__": value._meta.label_lower,
            "pk": make_json_safe(value.pk),
        }

    if isinstance(value, type) and issubclass(value, Model):
        return {
            "__model_class__": value._meta.label_lower,
        }

    if isinstance(value, QuerySet):
        return [_serialize_trigger_data(item) for item in value]

    if isinstance(value, dict):
        return {
            str(key): _serialize_trigger_data(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple, set)):
        return [_serialize_trigger_data(item) for item in value]

    return make_json_safe(value)

def _deserialize_trigger_data(value):
    if isinstance(value, dict):
        workflow_value = value.get("__workflow_value__")
        if workflow_value == "for_each_result":
            return ForEachResult(
                items=_deserialize_trigger_data(value.get("items", [])),
            )
        if workflow_value == "branch_stopped":
            return BranchStopped(reason=value.get("reason", "Condition did not match"))
        if workflow_value == "wait_for_other_branch":
            return WaitForOtherBranchResult(
                arrived_branch_ids=value.get("arrived_branch_ids", []),
                waiting_for_branch_ids=value.get("waiting_for_branch_ids", []),
            )
        model_label = value.get("__model__")
        if model_label:
            model = apps.get_model(model_label)
            if model is None:
                return None
            return model.objects.filter(pk=value.get("pk")).first()

        model_class_label = value.get("__model_class__")
        if model_class_label:
            return apps.get_model(model_class_label)

        return {
            key: _deserialize_trigger_data(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [_deserialize_trigger_data(item) for item in value]

    return value

def _summarize_output(output_data) -> dict:
    if isinstance(output_data, ForEachResult):
        return {
            "kind": "fanout",
            "item_count": len(output_data.items),
        }

    if isinstance(output_data, BranchStopped):
        return {
            "kind": "branch_stopped",
            "reason": output_data.reason,
        }

    if isinstance(output_data, WaitForOtherBranchResult):
        return {
            "kind": "waiting_for_branches",
            "arrived_branch_ids": output_data.arrived_branch_ids,
            "waiting_for_branch_ids": output_data.waiting_for_branch_ids,
        }

    if isinstance(output_data, list):
        return {
            "kind": "list",
            "item_count": len(output_data),
        }

    if isinstance(output_data, dict):
        return {
            "kind": "object",
            "keys": sorted(output_data.keys()),
        }

    return {
        "kind": type(output_data).__name__,
    }

def _trace_node(
    trace: list[dict],
    node: WorkflowNode,
    status: str,
    output_data=None,
    error: Exception | None = None,
) -> None:
    entry = {
        "node_id": node.id,
        "node_type": node.type,
        "node_sub_type": node.node_sub_type_id,
        "status": status,
    }
    if output_data is not None:
        if isinstance(
            output_data,
            (
                ForEachResult,
                BranchStopped,
                WaitForOtherBranchResult,
            ),
        ):
            entry["output"] = _summarize_output(output_data)
        else:
            entry["output"] = make_json_safe(output_data)
            entry["output_summary"] = _summarize_output(output_data)
    if error is not None:
        entry["error"] = str(error)
    trace.append(entry)

def _create_run_step(
    workflow_run: WorkflowRun,
    node: WorkflowNode,
    sequence: int,
    status: WorkflowRunStepStatus,
    state: WorkflowRunState,
    enable_logging: bool,
    output_data=_NO_OUTPUT,
) -> WorkflowRunStep | None:
    if not enable_logging:
        return None

    step = WorkflowRunStep(
        workflow_run=workflow_run,
        sequence=sequence,
        action_id=node.node_sub_type_id or str(node.id),
        status=status,
        node=node,
    )
    if output_data is not _NO_OUTPUT:
        serialized_output = _serialize_trigger_data(output_data)
        step.output_file.save(
            f"workflow-run-{workflow_run.pk}-step-{sequence}.json",
            ContentFile(json.dumps(serialized_output).encode("utf-8")),
            save=False,
        )
    step.save()
    state.current_step_id = step.id
    step.state = state.model_dump(mode="json")
    step.save(update_fields=["state", "datetime_updated"])
    return step

def _load_run_state(step: WorkflowRunStep) -> WorkflowRunState:
    if not step.state:
        raise ValueError("Workflow run step does not contain a resumable state.")

    return WorkflowRunState.model_validate(step.state)

def load_step_output(step: WorkflowRunStep) -> dict | Any:
    """Loads the output of a step into python

    Args:
        step (WorkflowRunStep): the workflow run step

    Raises:
        ValueError: raises when workflow does not contain step output

    Returns:
        dict | Any: the step output
    """
    if not step.output_file:
        raise ValueError("Workflow run step does not contain a stored output.")

    with step.output_file.open("rb") as output_file:
        return _deserialize_trigger_data(
            json.loads(output_file.read().decode("utf-8"))
        )

def _replace_step_output(step: WorkflowRunStep, output_data) -> None:
    serialized_output = _serialize_trigger_data(output_data)
    step.output_file.save(
        f"workflow-run-{step.workflow_run_id}-step-{step.sequence}.json",
        ContentFile(json.dumps(serialized_output).encode("utf-8")),
        save=False,
    )

def format_execution_trace(trace: list[dict]) -> str:
    parts = []
    for entry in trace:
        output = entry.get("output_summary") or {}
        output_kind = output.get("kind")
        suffix = f" ({output_kind})" if output_kind else ""
        parts.append(
            f"{entry['node_sub_type']}: {entry['status']}{suffix}"
        )
    return "; ".join(parts)

def serialize_workflow_run_result(workflow_run: WorkflowRun | None) -> dict | None:
    if workflow_run is None:
        return None

    return {
        "workflow_run_id": str(workflow_run.id),
    }


def _get_active_workflow(workflow: Workflow) -> Workflow | None:
    """Return the current database state only when the workflow is active."""
    return Workflow.objects.filter(pk=workflow.pk, active=True).first()


def run_workflow(
    workflow: Workflow,
    trigger_data: dict,
    start_node: WorkflowNode | None = None,
) -> WorkflowRun | None:
    """
    Initiates a workflow run for the given workflow.

    Args:
        workflow (Workflow): The workflow to be executed.
        start_node (WorkflowNode | None): Optional node to start from for debugging.
    """
    if start_node is not None and start_node.workflow_id != workflow.id:
        raise ValueError("Start node does not belong to the workflow.")

    workflow = _get_active_workflow(workflow)
    if workflow is None:
        return None

    if workflow.run_asynchronously:
        serialized_trigger_data = _serialize_trigger_data(trigger_data)
        if start_node is None:
            run_workflow_async.delay(workflow.id, serialized_trigger_data)
        else:
            run_workflow_async.delay(
                workflow.id,
                serialized_trigger_data,
                start_node.id,
            )
        return None

    return run_workflow_sync(workflow, trigger_data, start_node=start_node)

def _execute_workflow_state(
    workflow: Workflow,
    workflow_run: WorkflowRun,
    state: WorkflowRunState,
    start_frames: list[WorkflowExecutionFrame],
    related_object=None,
) -> WorkflowRun:
    execution_trace: list[dict] = []
    runtime_merge_outputs: dict[tuple[int, ScopeKey, int], object] = {}
    runtime_collect_outputs: dict[tuple[int, ScopeKey, int], object] = {}
    workflow_run.execution_trace = execution_trace

    def _scope_ancestors(
        scope_key: ScopeKey,
    ) -> list[ScopeKey]:
        return [
            scope_key[:length]
            for length in range(len(scope_key), -1, -1)
        ]

    def _scope_is_descendant(
        parent_scope: ScopeKey,
        child_scope: ScopeKey,
    ) -> bool:
        return (
            len(child_scope) > len(parent_scope)
            and child_scope[:len(parent_scope)] == parent_scope
        )

    def _effective_merge_branch_outputs(
        node: WorkflowNode,
        scope_key: ScopeKey,
        required_node_ids: list[int],
    ) -> dict[int, object]:
        branch_outputs: dict[int, object] = {}
        for branch_node_id in required_node_ids:
            for ancestor_scope in _scope_ancestors(scope_key):
                runtime_key = (node.id, ancestor_scope, branch_node_id)
                if runtime_key in runtime_merge_outputs:
                    branch_outputs[branch_node_id] = runtime_merge_outputs[runtime_key]
                    break

                merge_state = next(
                    (
                        item
                        for item in state.merge_states
                        if item.node_id == node.id and item.scope_key == ancestor_scope
                    ),
                    None,
                )
                if (
                    merge_state
                    and branch_node_id in merge_state.branch_output_step_ids
                ):
                    output_step = workflow_run.steps.get(
                        pk=merge_state.branch_output_step_ids[branch_node_id]
                    )
                    branch_outputs[branch_node_id] = load_step_output(output_step)
                    break

        return branch_outputs

    def _effective_collect_outputs(
        node: WorkflowNode,
        scope_key: ScopeKey,
        item_count: int,
    ) -> dict[int, object]:
        outputs: dict[int, object] = {}
        for index in range(item_count):
            runtime_key = (node.id, scope_key, index)
            if runtime_key in runtime_collect_outputs:
                outputs[index] = runtime_collect_outputs[runtime_key]
        return outputs

    # Create a recursive function
    def _execute_recursive(
        node: WorkflowNode,
        input_data,
        from_node: WorkflowNode | None = None,
        from_step: WorkflowRunStep | None = None,
        scope_key: ScopeKey = (),
    ) -> None:
        current_sequence = state.next_sequence
        state.next_sequence += 1
        state.current_node_id = node.id
        state.current_step_id = None
        state.from_node_id = from_node.id if from_node is not None else None
        state.scope_key = scope_key

        if node.node_sub_type_id == "MERGE_BRANCHES":
            incoming_edges = list(
                node.incoming_edges.select_related("from_node").order_by("id")
            )
            required_node_ids = [edge.from_node_id for edge in incoming_edges]
            merge_state = state.get_merge_state(node.id, scope_key)

            if merge_state.released:
                return

            if from_node is not None:
                runtime_merge_outputs[(node.id, scope_key, from_node.id)] = input_data
                if from_step is not None:
                    merge_state.branch_output_step_ids[from_node.id] = from_step.id

            branch_outputs = _effective_merge_branch_outputs(
                node,
                scope_key,
                required_node_ids,
            )
            arrived_branch_ids = sorted(branch_outputs.keys())
            waiting_for_branch_ids = [
                node_id for node_id in required_node_ids
                if node_id not in branch_outputs
            ]

            if waiting_for_branch_ids:
                wait_result = WaitForOtherBranchResult(
                    arrived_branch_ids=arrived_branch_ids,
                    waiting_for_branch_ids=waiting_for_branch_ids,
                )
                _trace_node(execution_trace, node, "success", output_data=wait_result)
                _create_run_step(
                    workflow_run=workflow_run,
                    node=node,
                    sequence=current_sequence,
                    status=WorkflowRunStepStatus.COMPLETED,
                    state=state,
                    enable_logging=workflow.enable_logging,
                    output_data=wait_result,
                )
                if from_node is not None:
                    for descendant_state in list(state.merge_states):
                        if (
                            descendant_state.node_id == node.id
                            and not descendant_state.released
                            and _scope_is_descendant(
                                scope_key,
                                descendant_state.scope_key,
                            )
                        ):
                            _execute_recursive(
                                node=node,
                                input_data={},
                                from_node=None,
                                from_step=None,
                                scope_key=descendant_state.scope_key,
                            )
                return

            merge_state.released = True
            input_data = {
                _node_input_key(edge.from_node): branch_outputs[edge.from_node_id]
                for edge in incoming_edges
            }

        if node.node_sub_type_id == "COLLECT":
            if not scope_key:
                raise ValueError("Collect must run inside a For Each branch.")

            fanout_node_id, item_index = scope_key[-1]
            parent_scope = scope_key[:-1]
            fanout_state = state.get_fanout_state(fanout_node_id, parent_scope)
            if fanout_state is None:
                raise ValueError("Collect could not find its parent For Each state.")

            collect_state = state.get_collect_state(
                node.id,
                fanout_node_id,
                parent_scope,
            )
            if collect_state.released:
                return

            runtime_collect_outputs[(node.id, parent_scope, item_index)] = input_data

            collected_outputs = _effective_collect_outputs(
                node,
                parent_scope,
                fanout_state.item_count,
            )
            waiting_for_item_indexes = [
                index
                for index in range(fanout_state.item_count)
                if index not in collected_outputs
            ]
            if waiting_for_item_indexes:
                state.next_sequence -= 1
                return

            collect_state.released = True
            input_data = [
                collected_outputs[index]
                for index in range(fanout_state.item_count)
            ]
            scope_key = parent_scope
            state.scope_key = parent_scope
        
        try:
            output_data = node.execute(input_data)
        except Exception as error:
            _trace_node(execution_trace, node, "error", error=error)
            _create_run_step(
                workflow_run=workflow_run,
                node=node,
                sequence=current_sequence,
                status=WorkflowRunStepStatus.FAILED,
                state=state,
                enable_logging=workflow.enable_logging,
            )
            raise

        if isinstance(output_data, ForEachResult):
            state.set_fanout_state(
                node.id,
                scope_key,
                len(output_data.items),
            )

        is_paused = node.node_sub_type_id == "HUMAN_IN_THE_LOOP"
        _trace_node(
            execution_trace,
            node,
            "paused" if is_paused else "success",
            output_data=output_data,
        )
        current_step = _create_run_step(
            workflow_run=workflow_run,
            node=node,
            sequence=current_sequence,
            status=(
                WorkflowRunStepStatus.PAUSED
                if is_paused
                else WorkflowRunStepStatus.COMPLETED
            ),
            state=state,
            enable_logging=workflow.enable_logging or is_paused,
            output_data=output_data,
        )
        if is_paused:
            raise _WorkflowPaused

        if isinstance(output_data, BranchStopped):
            return

        output_nodes = node.get_output_nodes()
        if not output_nodes:
            return

        if isinstance(output_data, ForEachResult):
            for index, item in enumerate(output_data.items):
                item_input = {
                    "item": item,
                    "index": index,
                }
                for output_node in output_nodes:
                    _execute_recursive(
                        node=output_node, 
                        input_data=item_input, 
                        from_node=node,
                        from_step=current_step,
                        scope_key=scope_key + ((node.id, index),),
                    )
            return

        if isinstance(output_data, WaitForOtherBranchResult):
            # Don't execute downstream nodes until the other branch has also reached this point
            return

        for output_node in output_nodes:
            _execute_recursive(
                node=output_node, 
                input_data=output_data, 
                from_node=node,
                from_step=current_step,
                scope_key=scope_key,
            )

    try:
        for frame in start_frames:
            _execute_recursive(
                node=frame.node,
                input_data=frame.input_data,
                from_node=frame.from_node,
                from_step=frame.from_step,
                scope_key=frame.scope_key,
            )
    except _WorkflowPaused:
        return workflow_run
    except Exception:
        publish_event(
            "workflow.result",
            workflow_run_id=str(workflow_run.id),
            status="failed",
            execution_trace=execution_trace,
            related_object=related_object,
            completed_at=timezone.now(),
        )
        raise

    publish_event(
        "workflow.result",
        workflow_run_id=str(workflow_run.id),
        status="successful",
        execution_trace=execution_trace,
        related_object=related_object,
        completed_at=timezone.now(),
    )

    return workflow_run

def run_workflow_sync(
    workflow: Workflow,
    trigger_data: dict,
    start_node: WorkflowNode | None = None,
) -> WorkflowRun | None:
    if start_node is not None and start_node.workflow_id != workflow.id:
        raise ValueError("Start node does not belong to the workflow.")

    workflow = _get_active_workflow(workflow)
    if workflow is None:
        return None

    workflow_run = WorkflowRun.objects.create(workflow=workflow)
    state = WorkflowRunState(
        workflow_id=workflow.id,
        workflow_run_id=workflow_run.id,
    )
    node = start_node or workflow.get_trigger()
    if node is None:
        raise ValueError("Workflow does not have a node to execute.")

    related_object = (
        trigger_data.get("instance")
        if isinstance(trigger_data, dict)
        else None
    )
    return _execute_workflow_state(
        workflow=workflow,
        workflow_run=workflow_run,
        state=state,
        start_frames=[WorkflowExecutionFrame(node=node, input_data=trigger_data)],
        related_object=related_object,
    )

def resume_workflow(
    paused_step: WorkflowRunStep,
    output_data=_NO_OUTPUT,
) -> WorkflowRun | None:
    """Resume immediately or dispatch through Celery based on the workflow."""
    paused_step = WorkflowRunStep.objects.select_related(
        "workflow_run__workflow"
    ).get(pk=paused_step.pk)
    if paused_step.status != WorkflowRunStepStatus.PAUSED:
        raise ValueError("Only paused workflow steps can be resumed.")

    if not paused_step.workflow_run.workflow.run_asynchronously:
        return resume_workflow_sync(paused_step, output_data=output_data)

    if output_data is _NO_OUTPUT:
        resume_workflow_async.delay(paused_step.pk)
    else:
        resume_workflow_async.delay(
            paused_step.pk,
            _serialize_trigger_data(output_data),
            True,
        )
    return None


def resume_workflow_sync(
    paused_step: WorkflowRunStep,
    output_data=_NO_OUTPUT,
) -> WorkflowRun:
    """Resume an existing workflow run after atomically claiming its paused step."""
    with transaction.atomic():
        paused_step = WorkflowRunStep.objects.select_for_update().select_related(
            "workflow_run__workflow"
        ).get(pk=paused_step.pk)
        if paused_step.status != WorkflowRunStepStatus.PAUSED:
            raise ValueError("Only paused workflow steps can be resumed.")

        workflow_run = WorkflowRun.objects.select_for_update().get(
            pk=paused_step.workflow_run_id
        )
        workflow = paused_step.workflow_run.workflow
        state = _load_run_state(paused_step)
        if state.workflow_id != workflow.id or state.workflow_run_id != workflow_run.id:
            raise ValueError("Workflow state does not match the paused workflow run.")

        latest_sequence = workflow_run.steps.aggregate(value=Max("sequence"))["value"]
        next_persisted_sequence = 0 if latest_sequence is None else latest_sequence + 1
        state.next_sequence = max(state.next_sequence, next_persisted_sequence)

        paused_node = workflow.nodes.filter(pk=state.current_node_id).first()
        if paused_node is None:
            raise ValueError("Paused workflow node no longer exists.")

        if output_data is _NO_OUTPUT:
            output_data = load_step_output(paused_step)
        else:
            _replace_step_output(paused_step, output_data)

        paused_step.status = WorkflowRunStepStatus.COMPLETED
        paused_step.save(
            update_fields=["status", "output_file", "datetime_updated"]
        )

        start_frames = [
            WorkflowExecutionFrame(
                node=output_node,
                input_data=output_data,
                from_node=paused_node,
                from_step=paused_step,
                scope_key=state.scope_key,
            )
            for output_node in paused_node.get_output_nodes()
        ]

    # Executors may handle database errors as workflow output. Run them after
    # the claim commits so a failed statement cannot poison the lock transaction.
    return _execute_workflow_state(
        workflow=workflow,
        workflow_run=workflow_run,
        state=state,
        start_frames=start_frames,
    )
