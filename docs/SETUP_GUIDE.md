\# CompeteIQ — Local Setup Guide



\## 1. Requirements



\- Windows

\- Python

\- Node.js and npm

\- Ollama

\- Visual Studio Code

\- Git



\## 2. Start Backend



Open a VS Code terminal:



```powershell

cd C:\\microsofthack\\backend

.\\venv\\Scripts\\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000

```



Backend URL:



http://127.0.0.1:8000



API documentation:



http://127.0.0.1:8000/docs



\## 3. Start Frontend



Open a second terminal:



```powershell

cd C:\\microsofthack\\frontend

npm.cmd run dev

```



Open the local URL displayed by Vite.



\## 4. Start BAND Worker



Open a third terminal:



```powershell

cd C:\\microsofthack\\backend

.\\venv\\Scripts\\python.exe band\_worker.py

```



\## 5. Check Ollama



Run:



```powershell

ollama list

```



Make sure Ollama is running and the configured model is available.



\## 6. Environment Configuration



Use a local .env file for API credentials and configuration.



Never upload .env files to GitHub.



\## 7. Troubleshooting



\- Check whether the backend is running.

\- Check the frontend URL.

\- Check backend CORS configuration if frontend requests fail.

\- Check Ollama and the configured model.

\- Check Hindsight credentials and endpoint.

\- Check BAND worker logs.



\## 8. Security



Never publish:

\- API keys

\- Passwords

\- Private environment files

\- Local databases

\- Personal credentials

