from typing import Dict, Optional
import asyncio
from datetime import datetime
import uuid

class TaskStatus:
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskManager:
    def __init__(self):
        self.tasks: Dict[str, Dict] = {}
        self.max_concurrent_tasks = 5
        self._semaphore = asyncio.Semaphore(self.max_concurrent_tasks)

    def create_task(self, icp: str, num_leads: int) -> str:
        """Create a new task and return its ID"""
        task_id = str(uuid.uuid4())
        self.tasks[task_id] = {
            "id": task_id,
            "icp": icp,
            "num_leads": num_leads,
            "status": TaskStatus.PENDING,
            "created_at": datetime.now().isoformat(),
            "completed_at": None,
            "result_file": None,
            "warning": None,
            "error": None
        }
        return task_id

    def update_task_status(self, task_id: str, status: str, result_file: Optional[str] = None, warning: Optional[str] = None, error: Optional[str] = None):
        """Update the status of a task"""
        if task_id in self.tasks:
            self.tasks[task_id].update({
                "status": status,
                "completed_at": datetime.now().isoformat() if status in [TaskStatus.COMPLETED, TaskStatus.FAILED] else None,
                "result_file": result_file if result_file else self.tasks[task_id]["result_file"],
                "warning": warning if warning is not None else self.tasks[task_id]["warning"],
                "error": error if error else self.tasks[task_id]["error"]
            })

    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Get the current status of a task"""
        return self.tasks.get(task_id)

    async def process_task(self, task_id: str, lead_generator):
        """Process a single task with semaphore control"""
        async with self._semaphore:
            try:
                task = self.tasks[task_id]
                self.update_task_status(task_id, TaskStatus.PROCESSING)
                
                # Generate leads - now returns tuple of (filepath, warning_message)
                result_file, warning_message = await lead_generator.generate_leads(
                    task["icp"],
                    task["num_leads"]
                )
                
                # Update task with both result file and warning message
                self.update_task_status(
                    task_id, 
                    TaskStatus.COMPLETED, 
                    result_file=result_file,
                    warning=warning_message
                )
                
            except Exception as e:
                self.update_task_status(task_id, TaskStatus.FAILED, error=str(e))
                raise

# Create a global task manager instance
task_manager = TaskManager()
