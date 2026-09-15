import os
import shutil

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from .settings import settings

from .agents.orchestrator import Orchestrator
from .registry import TaskRegistry


# ============================================================
# ORBIT APPLICATION
# ============================================================

app = FastAPI(
    title="ORBIT",
    description="Real-Time Multi-Agent AI Orchestration Platform",
    version="0.2.0",
)


# ============================================================
# CORS
# ============================================================
#
# Vite can use 5173, 5174, 5175, etc. when another port
# is already occupied.
#
# Instead of changing this every time, allow local frontend
# development ports.
#

# Dynamically configure allowed origins for local development.
# Reads from the ORIGINS environment variable (comma‑separated URLs).
# Falls back to the common Vite development ports if not set.
import os
origins_env = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:5174,http://localhost:5175,http://localhost:5199,http://127.0.0.1:5173,http://127.0.0.1:5174,http://127.0.0.1:5175,http://127.0.0.1:5199",
)
allow_origins = [origin.strip() for origin in origins_env.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ORCHESTRATOR
# ============================================================

orchestrator = Orchestrator(registry=TaskRegistry())


# ============================================================
# REQUEST MODEL
# ============================================================

class TaskRequest(BaseModel):
    task: str
    file_path: str | None = None

    @validator('task')
    def validate_task(cls, v: str) -> str:
        """Ensure the task string is non‑empty and not just whitespace, and enforce a length limit.

        The backend should reject empty or whitespace‑only tasks and overly long inputs.
        """
        if v is None:
            raise ValueError('Task must be provided')
        stripped = v.strip()
        if not stripped:
            raise ValueError('Task cannot be empty or whitespace')
        max_length = 1024
        if len(stripped) > max_length:
            raise ValueError(f'Task exceeds maximum length of {max_length} characters')
        return stripped

    @validator('file_path')
    def validate_file_path(cls, v: str | None) -> str | None:
        """Optional validation for file_path – ensure it is a non‑empty string when provided.
        """
        if v is None:
            return v
        if not v.strip():
            raise ValueError('file_path cannot be empty or whitespace')
        return v


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "name": "ORBIT",
        "status": "online",
        "version": "0.2.0",
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "healthy",
    }


# ============================================================
# RUN TASK
# ============================================================

import asyncio

@app.post("/run")
async def run_task(
    request: TaskRequest,
):
    """
    Run a task through the ORBIT orchestrator.

    Supports both:
        1. Normal research tasks without a file
        2. DATA / ML tasks with an optional file_path
    """

    # Create a new task entry in the registry and obtain a task ID
    task_id = orchestrator.registry.create_task(request.task)
    # Dispatch background execution
    asyncio.create_task(
        orchestrator.execute_task(task_id, request.task, request.file_path)
    )
    # Return the task identifier to the client for polling
    return {"task_id": task_id, "status": "queued"}

@app.get("/status/{task_id}")
async def get_status(task_id: str):
    """Retrieve the current status and details of a task by its ID."""
    task = orchestrator.registry.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.post("/api/contact")
async def contact(form: dict):
    """Accept contact form submissions (name, email, message). No persistence; just echo success."""
    # Basic validation
    required = ["name", "email", "message"]
    for field in required:
        if not form.get(field):
            raise HTTPException(status_code=400, detail=f"{field} is required")
    return {"status": "ok"}

@app.post("/api/waitlist")
async def waitlist(form: dict):
    """Accept waitlist email submissions. No persistence; just echo success."""
    email = form.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="email is required")
    return {"status": "ok"}


# ============================================================
# ANALYZE DATASET
# ============================================================

@app.post("/analyze")
async def analyze_dataset(
    task: str = Form(...),
    file: UploadFile = File(...),
):
    # --------------------------------------------------------
    # Create upload directory
    # --------------------------------------------------------

    upload_directory = "data/uploads"

    os.makedirs(
        upload_directory,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Protect against an empty filename
    # --------------------------------------------------------

    if not file.filename:
        return {
            "agent": "ORBIT",
            "task": task,
            "status": "error",
            "result": "Uploaded file has no filename.",
        }

    # --------------------------------------------------------
    # Build safe file path
    # --------------------------------------------------------

    file_path = os.path.join(
        upload_directory,
        os.path.basename(file.filename),
    )

    # --------------------------------------------------------
    # Save uploaded file
    # --------------------------------------------------------

    try:
        with open(
            file_path,
            "wb",
        ) as buffer:

            shutil.copyfileobj(
                file.file,
                buffer,
            )

    except Exception as error:

        return {
            "agent": "ORBIT",
            "task": task,
            "status": "error",
            "result": (
                f"Unable to save uploaded file: {error}"
            ),
        }

    # --------------------------------------------------------
    # Send task + file to Orchestrator
    # --------------------------------------------------------

    result = await orchestrator.route(
        task,
        file_path,
    )

    return result