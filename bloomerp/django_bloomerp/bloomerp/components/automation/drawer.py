from bloomerp.automation.registry import WORKFLOW_NODE_REGISTRY
from bloomerp.models.automation.workflow import Workflow
from bloomerp.router import router
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render


def _parse_bool(value: str | None) -> bool:
    return str(value).lower() in {"1", "true", "yes", "on"}


def _workflow_has_trigger(workflow_id: str | None) -> bool:
    if not workflow_id:
        return False

    workflow = get_object_or_404(Workflow, id=workflow_id)
    return workflow.nodes.filter(type="TRIGGER").exists()


@router.register(
    path="components/automation/drawer/",
    name="components_automation_drawer",
)
@login_required
def render_automation_drawer(request: HttpRequest) -> HttpResponse:
    workflow_id = request.GET.get("workflow_id")
    has_trigger = _parse_bool(request.GET.get("has_trigger")) or _workflow_has_trigger(workflow_id)
    excluded_types = {"TRIGGER"} if has_trigger else set()
    node_types = WORKFLOW_NODE_REGISTRY.grouped(exclude_types=excluded_types)

    return render(
        request,
        "components/automation/drawer.html",
        {
            "node_types": node_types,
            "has_trigger": has_trigger,
        },
    )
