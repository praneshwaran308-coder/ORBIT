import os
import shutil

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .agents.orchestrator import Orchestrator


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

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",

        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
    ],

    allow_credentials=True,

    allow_methods=[
        "*"
    ],

    allow_headers=[
        "*"
    ],
)


# ============================================================
# ORCHESTRATOR
# ============================================================

orchestrator = Orchestrator()


# ============================================================
# REQUEST MODEL
# ============================================================

class TaskRequest(BaseModel):
    task: str


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

@app.post("/run")
async def run_task(
    request: TaskRequest,
):
    result = await orchestrator.route(
        request.task
    )

    return result


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
    # Build file path
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