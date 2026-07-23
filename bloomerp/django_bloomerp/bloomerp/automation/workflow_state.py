from pydantic import BaseModel, Field


ScopeKey = tuple[tuple[int, int], ...]


class WorkflowMergeState(BaseModel):
    node_id: int
    scope_key: ScopeKey = ()
    branch_output_step_ids: dict[int, int] = Field(default_factory=dict)
    released: bool = False


class WorkflowFanoutState(BaseModel):
    node_id: int
    scope_key: ScopeKey = ()
    item_count: int


class WorkflowCollectState(BaseModel):
    node_id: int
    fanout_node_id: int
    scope_key: ScopeKey = ()
    released: bool = False


class WorkflowRunState(BaseModel):
    """Serializable control state for a workflow execution."""

    workflow_id: int
    workflow_run_id: int
    next_sequence: int = 0
    current_node_id: int | None = None
    current_step_id: int | None = None
    from_node_id: int | None = None
    scope_key: ScopeKey = ()
    merge_states: list[WorkflowMergeState] = Field(default_factory=list)
    fanout_states: list[WorkflowFanoutState] = Field(default_factory=list)
    collect_states: list[WorkflowCollectState] = Field(default_factory=list)

    def get_merge_state(
        self,
        node_id: int,
        scope_key: ScopeKey,
    ) -> WorkflowMergeState:
        for merge_state in self.merge_states:
            if merge_state.node_id == node_id and merge_state.scope_key == scope_key:
                return merge_state

        merge_state = WorkflowMergeState(node_id=node_id, scope_key=scope_key)
        self.merge_states.append(merge_state)
        return merge_state

    def set_fanout_state(
        self,
        node_id: int,
        scope_key: ScopeKey,
        item_count: int,
    ) -> WorkflowFanoutState:
        for fanout_state in self.fanout_states:
            if fanout_state.node_id == node_id and fanout_state.scope_key == scope_key:
                fanout_state.item_count = item_count
                return fanout_state

        fanout_state = WorkflowFanoutState(
            node_id=node_id,
            scope_key=scope_key,
            item_count=item_count,
        )
        self.fanout_states.append(fanout_state)
        return fanout_state

    def get_fanout_state(
        self,
        node_id: int,
        scope_key: ScopeKey,
    ) -> WorkflowFanoutState | None:
        return next(
            (
                fanout_state
                for fanout_state in self.fanout_states
                if fanout_state.node_id == node_id
                and fanout_state.scope_key == scope_key
            ),
            None,
        )

    def get_collect_state(
        self,
        node_id: int,
        fanout_node_id: int,
        scope_key: ScopeKey,
    ) -> WorkflowCollectState:
        for collect_state in self.collect_states:
            if (
                collect_state.node_id == node_id
                and collect_state.fanout_node_id == fanout_node_id
                and collect_state.scope_key == scope_key
            ):
                return collect_state

        collect_state = WorkflowCollectState(
            node_id=node_id,
            fanout_node_id=fanout_node_id,
            scope_key=scope_key,
        )
        self.collect_states.append(collect_state)
        return collect_state
