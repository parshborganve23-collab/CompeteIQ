# CompeteIQ — Local Setup Guide

## 1. Requirements

- Windows
- Python
- Node.js and npm
- Ollama
- VS Code

## 2. Start the Backend

Open a VS Code terminal:

```powershell
cd C:\microsofthack\backend
.\venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Backend address: http://127.0.0.1:8000

API documentation: http://127.0.0.1:8000/docs

## 3. Start the Frontend

Open a second terminal:

```powershell
cd C:\microsofthack\frontend
npm.cmd run dev
```

Open the local URL displayed by Vite in the terminal.

## 4. Start the BAND Worker

Open a third terminal:

```powershell
cd C:\microsofthack\backend
.\venv\Scripts\python.exe band_worker.py
```

## 5. Start Ollama

Make sure Ollama is running and the model configured by the project is available.

Check installed models:

```powershell
ollama list
```

## 6. Environment Configuration

Use a local `.env` file for required configuration and API credentials.

Do not upload `.env` to GitHub.

## 7. Troubleshooting

- If the frontend cannot connect, check that the backend is running.
- If the frontend port changes, check the backend CORS configuration.
- If the AI request fails, check Ollama and the configured model.
- If Hindsight operations fail, check its endpoint and credentials.
- If BAND execution fails, check the worker logs and its configuration.

## 8. Security

Never publish API keys, passwords, local databases, or private environment files.