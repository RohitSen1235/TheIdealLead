from typing import Dict, Optional, List
import asyncio
from datetime import datetime, timedelta
import uuid
import math
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import distinct
from models import DBTask

class TaskStatus:
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskManager:
    def __init__(self):
        self.tasks: Dict[str, Dict] = {}  # In-memory cache
        self.max_concurrent_tasks = 5
        self._semaphore = asyncio.Semaphore(self.max_concurrent_tasks)
        self.task_groups: Dict[str, List[str]] = {}  # Group ID -> List of task IDs
        self.group_seen_urls: Dict[str, set] = {}  # Group ID -> Set of seen URLs
        self.group_queries: Dict[str, List[str]] = {}  # Group ID -> List of search queries

    async def _generate_search_queries(self, lead_generator, icp: str) -> List[str]:
        """Generate search queries for a group - one unique query per task"""
        queries = await lead_generator.process_icp_to_search_query(icp)
        return queries[:5]  # Limit to 5 queries, one per task

    def create_distributed_tasks(self, db: Session, user_id: int, icp: str, num_leads: int, get_work_email: bool = False, get_phone_number: bool = False) -> str:
        """Create multiple tasks that distribute the workload and return group ID"""
        group_id = str(uuid.uuid4())
        self.task_groups[group_id] = []
        self.group_seen_urls[group_id] = set()
        self.group_queries[group_id] = []
        
        # Calculate profiles per task
        base_profiles_per_task = math.floor(num_leads / self.max_concurrent_tasks)
        remainder = num_leads % self.max_concurrent_tasks
        
        start_index = 0
        for i in range(self.max_concurrent_tasks):
            profiles_for_this_task = base_profiles_per_task + (1 if i < remainder else 0)
            
            if profiles_for_this_task > 0:
                task_id = str(uuid.uuid4())
                
                # Create database task
                db_task = DBTask(
                    id=task_id,
                    user_id=user_id,
                    group_id=group_id,
                    icp=icp,
                    total_leads_needed=num_leads,
                    leads_to_find=profiles_for_this_task,
                    leads_found=0,
                    start_index=start_index,
                    get_work_email=get_work_email,
                    get_phone_number=get_phone_number,
                    status=TaskStatus.PENDING
                )
                db.add(db_task)
                
                # Cache task in memory
                self.tasks[task_id] = {
                    "id": task_id,
                    "group_id": group_id,
                    "icp": icp,
                    "total_leads_needed": num_leads,
                    "leads_to_find": profiles_for_this_task,
                    "leads_found": 0,
                    "start_index": start_index,
                    "query_index": i,
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
        
        db.commit()
        return group_id

    def update_task_status(self, db: Session, task_id: str, status: str, result_file: Optional[str] = None, warning: Optional[str] = None, error: Optional[str] = None, leads_found: Optional[int] = None):
        """Update the status of a task in both cache and database"""
        # Update database
        db_task = db.query(DBTask).filter(DBTask.id == task_id).first()
        if db_task:
            db_task.status = status
            if leads_found is not None:
                db_task.leads_found = leads_found
            if status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                db_task.completed_at = datetime.now()
            if result_file:
                db_task.result_file = result_file
            if warning is not None:
                db_task.warning = warning
            if error:
                db_task.error = error
            db.commit()
        
        # Update cache
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

    def get_user_task_groups(self, db: Session, user_id: int) -> List[Dict]:
        """Get all task groups for a user"""
        # Get distinct group_ids for the user
        group_ids = db.query(distinct(DBTask.group_id)).filter(DBTask.user_id == user_id).all()
        group_ids = [group_id[0] for group_id in group_ids]  # Flatten results
        
        # Get status for each group
        groups = []
        for group_id in group_ids:
            group_status = self.get_group_status(db, group_id, user_id)
            if group_status:
                # Get the first task of the group for additional info
                first_task = db.query(DBTask).filter(
                    DBTask.group_id == group_id,
                    DBTask.user_id == user_id
                ).first()
                
                if first_task:
                    group_status.update({
                        "icp": first_task.icp,
                        "created_at": first_task.created_at.isoformat(),
                        "get_work_email": first_task.get_work_email,
                        "get_phone_number": first_task.get_phone_number
                    })
                    groups.append(group_status)
        
        # Sort by created_at descending
        groups.sort(key=lambda x: x["created_at"], reverse=True)
        return groups

    def get_group_status(self, db: Session, group_id: str, user_id: int) -> Optional[Dict]:
        """Get the combined status of all tasks in a group"""
        tasks = db.query(DBTask).filter(
            DBTask.group_id == group_id,
            DBTask.user_id == user_id
        ).all()
        
        if not tasks:
            return None
            
        total_leads_found = sum(task.leads_found for task in tasks)
        total_leads_needed = tasks[0].total_leads_needed
        all_result_files = [task.result_file for task in tasks if task.result_file]
        all_warnings = set(task.warning for task in tasks if task.warning)
        all_errors = set(task.error for task in tasks if task.error)
        task_statuses = {task.id: task.status for task in tasks}
        
        # Count task states
        active_tasks = sum(1 for task in tasks if task.status in [TaskStatus.PENDING, TaskStatus.PROCESSING])
        failed_tasks = sum(1 for task in tasks if task.status == TaskStatus.FAILED)
        completed_tasks = sum(1 for task in tasks if task.status == TaskStatus.COMPLETED)
        
        # Determine overall status
        if active_tasks > 0:
            combined_status = TaskStatus.PROCESSING
            status_message = f"Processing... Found {total_leads_found} profiles so far."
        elif completed_tasks + failed_tasks == len(tasks):
            if failed_tasks == len(tasks):
                combined_status = TaskStatus.FAILED
                status_message = "All tasks failed. Please try again."
            else:
                combined_status = TaskStatus.COMPLETED
                if total_leads_found >= total_leads_needed:
                    status_message = f"Successfully found all {total_leads_found} requested profiles!"
                    all_warnings.clear()
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
            "can_download": len(all_result_files) > 0
        }

    async def process_task(self, db: Session, task_id: str, lead_generator):
        """Process a single task with semaphore control"""
        async with self._semaphore:
            try:
                task = self.get_task_status(db, task_id, None)  # User ID not needed for processing
                if not task:
                    return
                    
                group_id = task["group_id"]
                self.update_task_status(db, task_id, TaskStatus.PROCESSING)
                
                # Generate queries for the group if not already done
                if not self.group_queries.get(group_id):
                    self.group_queries[group_id] = await self._generate_search_queries(lead_generator, task["icp"])
                
                # Get this task's specific query
                task_query = [self.group_queries[group_id][task["query_index"]]]
                
                # Pass single query and shared seen_urls set to lead generator
                result_file, message = await lead_generator.generate_leads(
                    task["icp"],
                    task["leads_to_find"],
                    get_work_email=task["get_work_email"],
                    get_phone_number=task["get_phone_number"],
                    start_index=task["start_index"],
                    seen_urls=self.group_seen_urls[group_id],
                    search_queries=task_query
                )
                
                # Extract number of leads found
                leads_found = 0
                if result_file:
                    import csv
                    with open(result_file, 'r') as csvfile:
                        leads_found = sum(1 for row in csv.DictReader(csvfile))
                
                self.update_task_status(
                    db,
                    task_id, 
                    TaskStatus.COMPLETED, 
                    result_file=result_file,
                    warning=message if leads_found < task["leads_to_find"] else None,
                    leads_found=leads_found
                )
                
            except Exception as e:
                self.update_task_status(db, task_id, TaskStatus.FAILED, error=str(e))
                return

    def get_task_status(self, db: Session, task_id: str, user_id: Optional[int]) -> Optional[Dict]:
        """Get the current status of a task"""
        # Try cache first
        if task_id in self.tasks:
            return self.tasks[task_id]
            
        # If not in cache, try database
        query = db.query(DBTask).filter(DBTask.id == task_id)
        if user_id is not None:
            query = query.filter(DBTask.user_id == user_id)
            
        db_task = query.first()
        
        if db_task:
            # Convert to dict format
            return {
                "id": db_task.id,
                "group_id": db_task.group_id,
                "icp": db_task.icp,
                "total_leads_needed": db_task.total_leads_needed,
                "leads_to_find": db_task.leads_to_find,
                "leads_found": db_task.leads_found,
                "start_index": db_task.start_index,
                "get_work_email": db_task.get_work_email,
                "get_phone_number": db_task.get_phone_number,
                "status": db_task.status,
                "created_at": db_task.created_at.isoformat(),
                "completed_at": db_task.completed_at.isoformat() if db_task.completed_at else None,
                "result_file": db_task.result_file,
                "warning": db_task.warning,
                "error": db_task.error
            }
        return None

    def cleanup_old_tasks(self, db: Session, max_age_hours: int = 24):
        """Clean up completed or failed tasks older than specified hours"""
        current_time = datetime.now()
        cutoff_time = current_time - timedelta(hours=max_age_hours)
        
        # Clean up database
        old_tasks = db.query(DBTask).filter(
            DBTask.status.in_([TaskStatus.COMPLETED, TaskStatus.FAILED]),
            DBTask.completed_at <= cutoff_time
        ).all()
        
        for task in old_tasks:
            # Clean up cache if present
            if task.id in self.tasks:
                del self.tasks[task.id]
            
            # Clean up group mappings
            if task.group_id in self.task_groups:
                self.task_groups[task.group_id].remove(task.id)
                if not self.task_groups[task.group_id]:
                    del self.task_groups[task.group_id]
                    if task.group_id in self.group_seen_urls:
                        del self.group_seen_urls[task.group_id]
                    if task.group_id in self.group_queries:
                        del self.group_queries[task.group_id]
            
            # Delete from database
            db.delete(task)
        
        db.commit()

# Create a global task manager instance
task_manager = TaskManager()
