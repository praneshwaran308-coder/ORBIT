// src/api/execution.js
// API client for task execution and status polling.
// Uses the backend FastAPI server (default http://localhost:8000).
// When VITE_USE_MOCK_EXECUTION=true, returns mock data for development.

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || (import.meta.env.MODE === 'production' ? '' : "http://localhost:8000");
const USE_MOCK = import.meta.env.VITE_USE_MOCK_EXECUTION === "true";

/**
 * Run a task on the backend.
 * @param {string} task - Description of the task.
 * @param {string|null} fileName - Optional uploaded file name (sent as file_path).
 * @returns {Promise<Object>} The JSON response containing task_id and status.
 */
export async function runTask(task, fileName = null) {
  if (USE_MOCK) {
    // Simulate a brief delay and return a mock task ID.
    await new Promise((r) => setTimeout(r, 200));
    return { task_id: `MOCK-${Date.now()}`, status: "queued" };
  }
  const payload = { task };
  if (fileName) payload.file_path = fileName;
  const response = await fetch(`${BACKEND_URL}/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const err = await response.text();
    throw new Error(`Run task failed: ${response.status} ${err}`);
  }
  return response.json();
}

/**
 * Retrieve the status of a task.
 * @param {string} taskId - The task identifier returned by apiRunTask.
 * @returns {Promise<Object>} The task status object from the backend.
 */
export async function getStatus(taskId) {
  if (USE_MOCK) {
    // Mock a completed task after a short delay.
    await new Promise((r) => setTimeout(r, 200));
    return { status: "completed", result: { result: "Mock result" }, activity: [] };
  }
  const response = await fetch(`${BACKEND_URL}/status/${taskId}`);
  if (!response.ok) {
    const err = await response.text();
    throw new Error(`Get status failed: ${response.status} ${err}`);
  }
  return response.json();
}
