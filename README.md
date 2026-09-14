# ORBIT

## Production Deployment

### Backend

Run the production server with:

`sh
uvicorn backend.main:app --host 0.0.0.0 --port 
`

The $Env:PORT environment variable is provided by Render. If not set, default to 8000.

### Frontend

Build the static assets and deploy to Vercel. The Vite build command:

`sh
npm run build
`

The dist/ folder is served by Vercel.

### Environment Variables

Create a .env file (or set env vars in the hosting platform) based on the .env.example file at the repository root. Important variables:

- ALLOWED_ORIGINS – comma-separated list of allowed origins for CORS.
- VITE_BACKEND_URL – URL of the backend (e.g., https://your-backend.onrender.com).

### Health Check

The backend exposes:

`
GET /health
`

which returns {  status: healthy }.

### API

- POST /run – submit a task.
- GET /status/{task_id} – poll task status.
- POST /analyze – upload a file and run analysis.

All endpoints respect the configured limits (max upload size, task length, etc.).

## Development

(Existing development instructions go here.)
