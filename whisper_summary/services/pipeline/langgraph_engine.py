"""LangGraph orchestration for the existing processing operations."""

from langgraph.graph import END, START, StateGraph

from whisper_summary.domain.tasks.models import Task
from whisper_summary.services.pipeline.engines import (
    LANGGRAPH_ENGINE,
    PipelineOperations,
    PipelineRuntime,
    PipelineState,
    ProcessingResult,
)


class LangGraphProcessingEngine:
    def __init__(self, runtime: PipelineRuntime):
        self.operations = PipelineOperations(runtime)
        builder = StateGraph(PipelineState)
        nodes = (
            ("download_media", self.operations.download_media),
            ("persist_resolved_title", self.operations.persist_resolved_title),
            ("transcribe_media", self.operations.transcribe_media),
            ("summarize_transcript", self.operations.summarize_transcript),
            ("save_local_artifacts", self.operations.save_local_artifacts),
            ("publish_summary", self.operations.publish_summary),
            ("complete_task", self.operations.complete_task),
            ("send_notification", self.operations.send_notification),
        )
        for name, node in nodes:
            builder.add_node(name, node)
        builder.add_edge(START, nodes[0][0])
        for (current, _), (following, _) in zip(nodes, nodes[1:]):
            builder.add_edge(current, following)
        builder.add_edge(nodes[-1][0], END)
        self.graph = builder.compile()

    def execute(self, task: Task) -> ProcessingResult:
        final_state = self.graph.invoke(
            self.operations.initial_state(task, LANGGRAPH_ENGINE)
        )
        return self.operations.result(final_state)
