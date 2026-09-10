# OWNIT - Local Development Guide

This guide provides clear, step-by-step instructions for setting up and running the OWNIT project locally on your machine.

---

## 📋 Prerequisites

Before starting, ensure you have the following installed on your system:

1. **Node.js** (v18 or higher): Check with `node -v`
2. **Python** (v3.10 or higher): Check with `python --version` or `py --list`
3. **Git**: Check with `git --version`
4. *(For future modules)* **MongoDB Community Server**: [Download](https://www.mongodb.com/try/download/community)
5. *(For future modules)* **Tesseract OCR**: [Download](https://github.com/UB-Mannheim/tesseract/wiki)
6. *(For future modules)* **Ollama**: [Download](https://ollama.ai/)

---

## 🚀 Setting Up the Backend

### Step 1: Open a Terminal and Navigate to Backend
```powershell
cd backend
```

### Step 2: Create a Python Virtual Environment
A virtual environment keeps your project dependencies isolated from the rest of your system.
```powershell
# Using Python 3.12 (recommended) or your default Python
py -3.12 -m venv .venv
```

### Step 3: Activate the Virtual Environment
```powershell
# On Windows PowerShell:
.venv\Scripts\Activate.ps1
```
*(If you see an execution policy error in PowerShell, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` and retry).*

### Step 4: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 5: Configure Environment Variables
Create your local `.env` file from the provided example:
```powershell
copy .env.example .env
```

### Step 6: Start the FastAPI Server
```powershell
uvicorn main:app --reload --port 8000
```

- **API Base URL**: `http://localhost:8000`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`
- **Health Check Endpoint**: `http://localhost:8000/api/health`

---

## 💻 Setting Up the Frontend

### Step 1: Open a New Terminal and Navigate to Frontend
```powershell
cd frontend
```

### Step 2: Install Node Modules
```powershell
npm install
```

### Step 3: Configure Environment Variables
Create your local `.env` file from the provided example:
```powershell
copy .env.example .env
```

### Step 4: Start the Development Server
```powershell
npm run dev
```

- **Frontend Application**: `http://localhost:5173`

---

## 🔍 Verifying the Setup

1. **Backend Verification**:
   - Open your browser and go to `http://localhost:8000/api/health`.
   - You should see:
     ```json
     {
       "status": "healthy",
       "project": "OWNIT",
       "tagline": "Own More. Worry Less.",
       "version": "0.1.0"
     }
     ```

2. **Frontend Verification**:
   - Open your browser and go to `http://localhost:5173`.
   - You should see the welcome initialization screen for OWNIT with system status indicators.

---

## 💡 Troubleshooting & Tips

- **PowerShell Script Execution Error**: If `.venv\Scripts\Activate.ps1` gives a security permission error, run:
  ```powershell
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
  ```
- **Port Conflicts**: If port `8000` or `5173` is already in use, you can adjust them in `.env` or in `vite.config.js` / uvicorn command line.
