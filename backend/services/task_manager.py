from typing import Dict, Optional, List
import asyncio
from datetime import datetime
import uuid
import math

class TaskStatus:
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskManager:
    def __init__(self):
        self.tasks: Dict[str, Dict] = {}
        self.max_concurrent_tasks = 3
        self._semaphore = asyncio.Semaphore(self.max_concurrent_tasks)
        self.task_groups: Dict[str, List[str]] = {}  # Group ID -> List of task IDs

    def create_distributed_tasks(self, icp: str, num_leads: int) -> str:
        """Create multiple tasks that distribute the workload and return group ID"""
        group_id = str(uuid.uuid4())
        self.task_groups[group_id] = []
        
        # Calculate profiles per task
        base_profiles_per_task = math.floor(num_leads / self.max_concurrent_tasks)
        remainder = num_leads % self.max_concurrent_tasks
        
        start_index = 0
        for i in range(self.max_concurrent_tasks):
            # Add one extra profile to tasks until remainder is distributed
            profiles_for_this_task = base_profiles_per_task + (1 if i < remainder else 0)
            
            if profiles_for_this_task > 0:
                task_id = str(uuid.uuid4())
                self.tasks[task_id] = {
                    "id": task_id,
                    "group_id": group_id,
                    "icp": icp,
                    "total_leads_needed": num_leads,
                    "leads_to_find": profiles_for_this_task,
                    "start_index": start_index,
                    "status": TaskStatus.PENDING,
                    "created_at": datetime.now().isoformat(),
                    "completed_at": None,
                    "result_file": None,
                    "warning": None,
                    "error": None
                }
                self.task_groups[group_id].append(task_id)
                start_index += profiles_for_this_task
        
        return group_id

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

    def get_group_status(self, group_id: str) -> Dict:
        """Get the combined status of all tasks in a group"""
        if group_id not in self.task_groups:
            return None
            
        task_ids = self.task_groups[group_id]
        total_leads_found = 0
        all_result_files = []
        all_warnings = []
        combined_status = TaskStatus.COMPLETED
        
        for task_id in task_ids:
            task = self.tasks[task_id]
            if task["status"] == TaskStatus.FAILED:
                combined_status = TaskStatus.FAILED
                break
            elif task["status"] in [TaskStatus.PENDING, TaskStatus.PROCESSING]:
                combined_status = TaskStatus.PROCESSING
            
            if task["result_file"]:
                all_result_files.append(task["result_file"])
            if task["warning"]:
                all_warnings.append(task["warning"])
        
        return {
            "group_id": group_id,
            "status": combined_status,
            "result_files": all_result_files,
            "warnings": all_warnings,
            "task_statuses": {task_id: self.tasks[task_id]["status"] for task_id in task_ids}
        }

    async def process_task(self, task_id: str, lead_generator):
        """Process a single task with semaphore control"""
        async with self._semaphore:
            try:
                task = self.tasks[task_id]
                self.update_task_status(task_id, TaskStatus.PROCESSING)
                
                # Generate leads with specific range for this task
                result_file, warning_message = await lead_generator.generate_leads(
                    task["icp"],
                    task["leads_to_find"],
                    task["start_index"]
                )
                
                self.update_task_status(
                    task_id, 
                    TaskStatus.COMPLETED, 
                    result_file=result_file,
                    warning=warning_message
                )
                
            except Exception as e:
                self.update_task_status(task_id, TaskStatus.FAILED, error=str(e))
                raise

    def cleanup_old_tasks(self, max_age_hours: int = 24):
        """Clean up completed or failed tasks older than specified hours"""
        current_time = datetime.now()
        to_remove = []
        groups_to_remove = []
        
        for task_id, task in self.tasks.items():
            if task["status"] in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                completed_at = datetime.fromisoformat(task["completed_at"])
                age = (current_time - completed_at).total_seconds() / 3600
                
                if age > max_age_hours:
                    to_remove.append(task_id)
                    group_id = task.get("group_id")
                    if group_id and group_id not in groups_to_remove:
                        groups_to_remove.append(group_id)
        
        for task_id in to_remove:
            del self.tasks[task_id]
            
        for group_id in groups_to_remove:
            if group_id in self.task_groups:
                del self.task_groups[group_id]

# Create a global task manager instance
task_manager = TaskManager()
