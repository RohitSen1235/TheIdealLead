from typing import Dict, Optional, List
import asyncio
from datetime import datetime
import uuid
import math
from collections import defaultdict

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
        self.task_groups: Dict[str, List[str]] = {}  # Group ID -> List of task IDs
        self.group_seen_urls: Dict[str, set] = {}  # Group ID -> Set of seen URLs
        self.group_queries: Dict[str, List[str]] = {}  # Group ID -> List of search queries

    async def _generate_search_queries(self, lead_generator, icp: str) -> List[str]:
        """Generate search queries for a group - one unique query per task"""
        # Generate exactly 5 queries (one per potential task)
        queries = await lead_generator.process_icp_to_search_query(icp)
        return queries[:5]  # Limit to 5 queries, one per task

    def create_distributed_tasks(self, icp: str, num_leads: int, get_work_email: bool = False, get_phone_number: bool = False) -> str:
        """Create multiple tasks that distribute the workload and return group ID"""
        group_id = str(uuid.uuid4())
        self.task_groups[group_id] = []
        self.group_seen_urls[group_id] = set()  # Initialize empty set for this group
        self.group_queries[group_id] = []  # Initialize empty list for search queries
        
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
                    "leads_found": 0,
                    "start_index": start_index,
                    "query_index": i,  # Store task's index for query distribution
                    "get_work_email": get_work_email,
                    "get_phone_number": get_phone_number,
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

    def update_task_status(self, task_id: str, status: str, result_file: Optional[str] = None, warning: Optional[str] = None, error: Optional[str] = None, leads_found: Optional[int] = None):
        """Update the status of a task"""
        if task_id in self.tasks:
            if leads_found is not None:
                self.tasks[task_id]["leads_found"] = leads_found
                
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
        total_leads_needed = 0
        all_result_files = []
        all_warnings = set()  # Use set to avoid duplicates
        all_errors = set()    # Use set to avoid duplicates
        task_statuses = {}
        
        # Count active and failed tasks
        active_tasks = 0
        failed_tasks = 0
        completed_tasks = 0
        
        for task_id in task_ids:
            task = self.tasks[task_id]
            total_leads_found += task["leads_found"]
            total_leads_needed += task["leads_to_find"]
            
            if task["status"] == TaskStatus.FAILED:
                failed_tasks += 1
                if task["error"]:
                    all_errors.add(f"Task {task_ids.index(task_id) + 1}: {task['error']}")
            elif task["status"] in [TaskStatus.PENDING, TaskStatus.PROCESSING]:
                active_tasks += 1
            elif task["status"] == TaskStatus.COMPLETED:
                completed_tasks += 1
            
            if task["result_file"]:
                all_result_files.append(task["result_file"])
            if task["warning"]:
                all_warnings.add(task["warning"])
                
            task_statuses[task_id] = task["status"]
        
        # Determine overall status
        if active_tasks > 0:
            combined_status = TaskStatus.PROCESSING
            status_message = f"Processing... Found {total_leads_found} profiles so far."
        elif completed_tasks + failed_tasks == len(task_ids):
            if failed_tasks == len(task_ids):
                combined_status = TaskStatus.FAILED
                status_message = "All tasks failed. Please try again."
            else:
                combined_status = TaskStatus.COMPLETED
                if total_leads_found >= total_leads_needed:
                    status_message = f"Successfully found all {total_leads_found} requested profiles!"
                    all_warnings.clear()  # Clear warnings if we got all profiles
                else:
                    status_message = f"Found {total_leads_found} out of {total_leads_needed} requested profiles."
                    if failed_tasks > 0:
                        status_message += f" ({failed_tasks} task(s) failed)"
        else:
            combined_status = TaskStatus.PROCESSING
            status_message = f"Processing... Found {total_leads_found} profiles so far."
        
        return {
            "group_id": group_id,
            "status": combined_status,
            "status_message": status_message,
            "total_leads_found": total_leads_found,
            "total_leads_needed": total_leads_needed,
            "result_files": all_result_files,
            "warnings": sorted(all_warnings) if all_warnings else [],
            "errors": sorted(all_errors) if all_errors else [],
            "task_statuses": task_statuses,
            "can_download": len(all_result_files) > 0  # Allow download if we have any results
        }

    async def process_task(self, task_id: str, lead_generator):
        """Process a single task with semaphore control"""
        async with self._semaphore:
            try:
                task = self.tasks[task_id]
                group_id = task["group_id"]
                self.update_task_status(task_id, TaskStatus.PROCESSING)
                
                # Generate queries for the group if not already done
                if not self.group_queries.get(group_id):
                    self.group_queries[group_id] = await self._generate_search_queries(lead_generator, task["icp"])
                
                # Get this task's specific query (one query per task)
                task_query = [self.group_queries[group_id][task["query_index"]]]
                
                # Pass single query and shared seen_urls set to lead generator
                result_file, message = await lead_generator.generate_leads(
                    task["icp"],
                    task["leads_to_find"],
                    get_work_email=task["get_work_email"],
                    get_phone_number=task["get_phone_number"],
                    start_index=task["start_index"],
                    seen_urls=self.group_seen_urls[group_id],
                    search_queries=task_query  # Pass single query as a list
                )
                
                # Extract number of leads found
                leads_found = 0
                if result_file:
                    import csv
                    with open(result_file, 'r') as csvfile:
                        leads_found = sum(1 for row in csv.DictReader(csvfile))
                
                self.update_task_status(
                    task_id, 
                    TaskStatus.COMPLETED, 
                    result_file=result_file,
                    warning=message if leads_found < task["leads_to_find"] else None,
                    leads_found=leads_found
                )
                
            except Exception as e:
                self.update_task_status(task_id, TaskStatus.FAILED, error=str(e))
                return

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
                if group_id in self.group_seen_urls:
                    del self.group_seen_urls[group_id]
                if group_id in self.group_queries:
                    del self.group_queries[group_id]

# Create a global task manager instance
task_manager = TaskManager()
