import uuid
import datetime
import threading
from typing import Dict, Any, Optional


class TaskRegistry:
    def __init__(self):
        self._tasks: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def create_task(self, description: str) -> str:
        task_id = str(uuid.uuid4())
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        task = {
            "task_id": task_id,
            "description": description,
            "status": "queued",
            "agents": [],
            "activity": [],
            "result": None,
            "error": None,
            "started_at": now,
            "completed_at": None,
        }
        with self._lock:
            self._tasks[task_id] = task
        return task_id

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._tasks.get(task_id)

    def update_task(self, task_id: str, **updates) -> None:
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id].update(updates)

    def add_agent(self, task_id: str, name: str) -> None:
        with self._lock:
            task = self._tasks.get(task_id)
            if task:
                task.setdefault("agents", []).append({"name": name, "status": "queued"})

    def set_agent_status(self, task_id: str, name: str, status: str) -> None:
        with self._lock:
            task = self._tasks.get(task_id)
            if task:
                for agent in task.get("agents", []):
                    if agent["name"] == name:
                        agent["status"] = status
                        break
                else:
                    task.setdefault("agents", []).append({"name": name, "status": status})

    def add_activity(self, task_id: str, message: str) -> None:
        with self._lock:
            task = self._tasks.get(task_id)
            if task:
                task.setdefault("activity", []).append({"timestamp": datetime.datetime.utcnow().isoformat() + 'Z', "message": message})

    def set_result(self, task_id: str, result: Any) -> None:
        with self._lock:
            task = self._tasks.get(task_id)
            if task:
                task["result"] = result
                task["status"] = "completed"
                task["completed_at"] = datetime.datetime.utcnow().isoformat() + 'Z'

    def set_error(self, task_id: str, error: str) -> None:
        with self._lock:
            task = self._tasks.get(task_id)
            if task:
                task["error"] = error
                task["status"] = "failed"
                task["completed_at"] = datetime.datetime.utcnow().isoformat() + 'Z'
