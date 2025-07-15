"""Background task queue system for handling heavy operations."""

import asyncio
import logging
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task status enumeration."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """Task data class."""

    id: str
    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Any = None
    error: Optional[str] = None
    priority: int = 0
    retries: int = 0
    max_retries: int = 3
    timeout: Optional[int] = None


class TaskQueue:
    """Background task queue for handling heavy operations."""

    def __init__(self, max_workers: int = 4, max_queue_size: int = 1000):
        """
        Initialize the task queue.

        Args:
            max_workers: Maximum number of concurrent workers
            max_queue_size: Maximum number of tasks in queue
        """
        self.max_workers = max_workers
        self.max_queue_size = max_queue_size
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self.tasks: Dict[str, Task] = {}
        self.workers: List[asyncio.Task] = []
        self.running = False
        self._task_counter = 0

    async def start(self):
        """Start the task queue workers."""
        if self.running:
            logger.warning("Task queue is already running")
            return

        self.running = True
        logger.info(f"Starting task queue with {self.max_workers} workers")

        # Start worker tasks
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self.workers.append(worker)

        logger.info("Task queue started successfully")

    async def stop(self):
        """Stop the task queue workers."""
        if not self.running:
            return

        logger.info("Stopping task queue...")
        self.running = False

        # Cancel all workers
        for worker in self.workers:
            worker.cancel()

        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers.clear()

        logger.info("Task queue stopped")

    async def add_task(
        self,
        func: Callable,
        *args,
        priority: int = 0,
        timeout: Optional[int] = None,
        max_retries: int = 3,
        **kwargs,
    ) -> str:
        """
        Add a task to the queue.

        Args:
            func: Function to execute
            *args: Function arguments
            priority: Task priority (higher = more important)
            timeout: Task timeout in seconds
            max_retries: Maximum number of retries
            **kwargs: Function keyword arguments

        Returns:
            Task ID
        """
        if not self.running:
            raise RuntimeError("Task queue is not running")

        self._task_counter += 1
        task_id = f"task-{self._task_counter}-{int(time.time())}"

        task = Task(
            id=task_id,
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority,
            timeout=timeout,
            max_retries=max_retries,
        )

        self.tasks[task_id] = task

        # Add to queue with priority
        await self.queue.put((priority, task))

        logger.info(f"Added task {task_id} to queue")
        return task_id

    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a task.

        Args:
            task_id: Task ID

        Returns:
            Task status dictionary or None if not found
        """
        task = self.tasks.get(task_id)
        if not task:
            return None

        return {
            "id": task.id,
            "status": task.status.value,
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": (
                task.completed_at.isoformat() if task.completed_at else None
            ),
            "result": task.result,
            "error": task.error,
            "retries": task.retries,
            "max_retries": task.max_retries,
        }

    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a pending task.

        Args:
            task_id: Task ID

        Returns:
            True if cancelled, False if not found or already running
        """
        task = self.tasks.get(task_id)
        if not task or task.status != TaskStatus.PENDING:
            return False

        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.now()
        logger.info(f"Cancelled task {task_id}")
        return True

    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        pending = len(
            [t for t in self.tasks.values() if t.status == TaskStatus.PENDING]
        )
        running = len(
            [t for t in self.tasks.values() if t.status == TaskStatus.RUNNING]
        )
        completed = len(
            [t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED]
        )
        failed = len([t for t in self.tasks.values() if t.status == TaskStatus.FAILED])
        cancelled = len(
            [t for t in self.tasks.values() if t.status == TaskStatus.CANCELLED]
        )

        return {
            "queue_size": self.queue.qsize(),
            "max_queue_size": self.max_queue_size,
            "active_workers": len(self.workers),
            "max_workers": self.max_workers,
            "tasks": {
                "pending": pending,
                "running": running,
                "completed": completed,
                "failed": failed,
                "cancelled": cancelled,
                "total": len(self.tasks),
            },
        }

    async def _worker(self, worker_name: str):
        """Worker function that processes tasks."""
        logger.info(f"Worker {worker_name} started")

        while self.running:
            try:
                # Get task from queue
                priority, task = await asyncio.wait_for(self.queue.get(), timeout=1.0)

                if task.status == TaskStatus.CANCELLED:
                    continue

                await self._execute_task(task, worker_name)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Worker {worker_name} error: {e}")

        logger.info(f"Worker {worker_name} stopped")

    async def _execute_task(self, task: Task, worker_name: str):
        """Execute a single task."""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()

        logger.info(f"Worker {worker_name} executing task {task.id}")

        try:
            # Execute the task with timeout if specified
            if task.timeout:
                result = await asyncio.wait_for(
                    self._run_function(task.func, *task.args, **task.kwargs),
                    timeout=task.timeout,
                )
            else:
                result = await self._run_function(task.func, *task.args, **task.kwargs)

            task.result = result
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()

            logger.info(f"Task {task.id} completed successfully")

        except asyncio.TimeoutError:
            task.error = f"Task timed out after {task.timeout} seconds"
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            logger.error(f"Task {task.id} timed out")

        except Exception as e:
            task.error = str(e)
            task.retries += 1

            if task.retries < task.max_retries:
                # Retry the task
                task.status = TaskStatus.PENDING
                await self.queue.put((task.priority, task))
                logger.warning(
                    f"Task {task.id} failed, retrying ({task.retries}/{task.max_retries})"
                )
            else:
                # Max retries reached
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.now()
                logger.error(
                    f"Task {task.id} failed after {task.max_retries} retries: {e}"
                )

    async def _run_function(self, func: Callable, *args, **kwargs) -> Any:
        """Run a function, handling both sync and async functions."""
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            # Run sync function in thread pool
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, func, *args, **kwargs)

    async def cleanup_old_tasks(self, max_age_hours: int = 24):
        """Clean up old completed tasks."""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        tasks_to_remove = []

        for task_id, task in self.tasks.items():
            if (
                task.status
                in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
                and task.completed_at
                and task.completed_at < cutoff_time
            ):
                tasks_to_remove.append(task_id)

        for task_id in tasks_to_remove:
            del self.tasks[task_id]

        if tasks_to_remove:
            logger.info(f"Cleaned up {len(tasks_to_remove)} old tasks")


# Global task queue instance
task_queue = TaskQueue()


# Decorator for easy task submission
def background_task(
    priority: int = 0, timeout: Optional[int] = None, max_retries: int = 3
):
    """
    Decorator to submit a function as a background task.

    Args:
        priority: Task priority
        timeout: Task timeout in seconds
        max_retries: Maximum number of retries
    """

    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            task_id = await task_queue.add_task(
                func,
                *args,
                priority=priority,
                timeout=timeout,
                max_retries=max_retries,
                **kwargs,
            )
            return task_id

        return wrapper

    return decorator
