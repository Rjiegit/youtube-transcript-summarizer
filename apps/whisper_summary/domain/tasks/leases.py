class TaskLeaseLostError(RuntimeError):
    """Raised when a worker no longer owns the task it is processing."""
