# scripts/production_hardening_check.py
"""Run production hardening verification checks for ORBIT.
Prints a markdown table with PASS/FAIL for each category.
"""
import asyncio, os, json, sys
from typing import List
import httpx

BASE_URL = os.getenv("VITE_BACKEND_URL", "http://127.0.0.1:8000")

async def post_run(task_text: str, file_path: str | None = None):
    payload = {"task": task_text}
    if file_path:
        payload["file_path"] = file_path
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{BASE_URL}/run", json=payload)
    return resp

async def get_status(task_id: str):
    async with httpx.AsyncClient() as client:
        return await client.get(f"{BASE_URL}/status/{task_id}")

async def check_task_registry():
    # create two tasks concurrently
    task1 = asyncio.create_task(post_run("Task A"))
    task2 = asyncio.create_task(post_run("Task B"))
    r1, r2 = await asyncio.gather(task1, task2)
    if r1.status_code != 200 or r2.status_code != 200:
        return False
    id1 = r1.json().get("task_id")
    id2 = r2.json().get("task_id")
    if not id1 or not id2 or id1 == id2:
        return False
    # poll both until completed (timeout 30s)
    async def wait_complete(task_id):
        for _ in range(30):
            resp = await get_status(task_id)
            if resp.status_code == 200 and resp.json().get("status") == "completed":
                return True
            await asyncio.sleep(1)
        return False
    done = await asyncio.gather(wait_complete(id1), wait_complete(id2))
    return all(done)

async def check_api_validation():
    async with httpx.AsyncClient() as client:
        # empty task
        r = await client.post(f"{BASE_URL}/run", json={"task": ""})
        if r.status_code == 200:
            return False
        # whitespace task
        r = await client.post(f"{BASE_URL}/run", json={"task": "   "})
        if r.status_code == 200:
            return False
        # nonexistent task id
        r = await client.get(f"{BASE_URL}/status/nonexistent-id")
        if r.status_code == 200 and "error" not in r.json():
            return False
        # malformed request (missing JSON)
        r = await client.post(f"{BASE_URL}/run", content="notjson")
        if r.status_code == 200:
            return False
        # oversized input (1MB string)
        big = "x" * (1024 * 1024)
        r = await client.post(f"{BASE_URL}/run", json={"task": big})
        if r.status_code == 200:
            return False
    return True

async def check_cors_env():
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("settings", os.path.abspath("backend/settings.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        origins = getattr(mod, "allow_origins", [])
        if "*" in origins:
            return False
        env_path = os.path.abspath("frontend/.env.example")
        with open(env_path) as f:
            content = f.read()
        if "VITE_BACKEND_URL" not in content:
            return False
        return True
    except Exception:
        return False

async def check_file_upload():
    import tempfile
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
    tmp.write(b"sample data")
    tmp.close()
    async with httpx.AsyncClient() as client:
        with open(tmp.name, "rb") as f:
            files = {"file": (os.path.basename(tmp.name), f, "text/plain")}
            data = {"task": "test upload"}
            resp = await client.post(f"{BASE_URL}/analyze", data=data, files=files)
    os.unlink(tmp.name)
    return resp.status_code == 200 and "result" in resp.json()

async def check_health():
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE_URL}/health")
    return r.status_code == 200 and r.json().get("status") == "healthy"

async def main():
    results = {}
    results["REGISTRY"] = await check_task_registry()
    results["API VALIDATION"] = await check_api_validation()
    results["CORS/ENV"] = await check_cors_env()
    results["FILE UPLOAD"] = await check_file_upload()
    results["HEALTH"] = await check_health()
    print("# Production Hardening Verification Results")
    for key, ok in results.items():
        print(f"- {key}: {'PASS' if ok else 'FAIL'}")

if __name__ == "__main__":
    asyncio.run(main())
