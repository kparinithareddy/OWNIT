# OWNIT - Setup & Installation Guide

> **Environment**: Windows, macOS, or Linux  
> **Target Audience**: Students, Evaluators, and Developers setting up OWNIT from scratch

---

## 1. Prerequisites Checklist

Before setting up OWNIT, ensure the following tools are installed on your machine:

| Prerequisite | Minimum Version | Verification Command | Download / Install Link |
|:---|:---|:---|:---|
| **Python** | 3.10+ (Recommended: 3.12) | `python --version` | [python.org](https://www.python.org/downloads/) |
| **Node.js** | 18+ (Recommended: 20 LTS) | `node --version` | [nodejs.org](https://nodejs.org/) |
| **MongoDB** | Community Server 6.0+ | `mongod --version` | [mongodb.com](https://www.mongodb.com/try/download/community) |
| **Git** | 2.30+ | `git --version` | [git-scm.com](https://git-scm.com/) |
| **Tesseract OCR** *(Optional)* | 5.0+ | `tesseract --version` | [UB-Mannheim Tesseract](https://github.com/UB-Mannheim/tesseract/wiki) |
| **Ollama** *(Optional)* | Latest | `ollama --version` | [ollama.com](https://ollama.com/) |

---

## 2. Step-by-Step Installation

### Step 1: Clone the Repository
```bash
git clone https://github.com/kparinithareddy/OWNIT.git
cd OWNIT
```

---

### Step 2: Configure & Start MongoDB
1. Ensure the MongoDB service is running on your machine:
   - **Windows**: Verify `MongoDB` is running in `services.msc` or run `net start MongoDB`.
   - **Linux/macOS**: `sudo systemctl start mongod` or `brew services start mongodb-community`.
2. Default connection string: `mongodb://localhost:27017`

---

### Step 3: Backend Setup (FastAPI)

1. Open a terminal and navigate to the `backend` folder:
   ```powershell
   cd backend
   ```

2. Create and activate a Python virtual environment:
   - **Windows (PowerShell)**:
     ```powershell
     python -m venv .venv
     .venv\Scripts\Activate.ps1
     ```
   - **macOS / Linux**:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. Install required Python packages:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. Configure Environment Variables:
   - Copy the example environment file:
     ```powershell
     Copy-Item .env.example .env
     ```
   - Default `.env` values:
     ```ini
     PORT=8000
     ENVIRONMENT=development
     MONGODB_URI=mongodb://localhost:27017
     MONGODB_DB_NAME=ownit
     JWT_SECRET=supersecretjwtkey_ownit_college_project_2026
     JWT_ALGORITHM=HS256
     ACCESS_TOKEN_EXPIRE_MINUTES=1440
     UPLOAD_DIR=uploads
     MAX_UPLOAD_SIZE_BYTES=10485760
     OLLAMA_BASE_URL=http://localhost:11434
     OLLAMA_MODEL=llama3.2
     ```

5. Start the Backend API Server:
   ```bash
   uvicorn main:app --reload --port 8000
   ```
   - Access Swagger API Docs at: [http://localhost:8000/docs](http://localhost:8000/docs)

---

### Step 4: Frontend Setup (React + Vite)

1. Open a second terminal and navigate to the `frontend` folder:
   ```powershell
   cd frontend
   ```

2. Install Node.js dependencies:
   ```bash
   npm install
   ```

3. Configure Environment Variables:
   - Copy the example environment file:
     ```powershell
     Copy-Item .env.example .env
     ```
   - Default `frontend/.env` values:
     ```ini
     VITE_API_BASE_URL=http://localhost:8000
     ```

4. Start the Frontend Development Server:
   ```bash
   npm run dev
   ```
   - Access the Web Application at: [http://localhost:5173](http://localhost:5173)

---

### Step 5: Optional Local Engines Setup

#### A. Tesseract OCR (For scanned paper receipt images)
1. Install Tesseract OCR from [UB-Mannheim](https://github.com/UB-Mannheim/tesseract/wiki).
2. Add `C:\Program Files\Tesseract-OCR` to your system `PATH` environment variable.
3. Verify via command prompt: `tesseract --version`.

#### B. Ollama Local LLM (For conversational AI)
1. Install Ollama from [ollama.com](https://ollama.com/).
2. Pull the lightweight, high-performance Llama 3.2 model:
   ```bash
   ollama pull llama3.2
   ```
3. Ollama runs in the background on port `11434`.
4. *Note: If Ollama is not installed, OWNIT automatically uses deterministic rule-based analysis without crashing.*

---

## 3. Verifying the Complete Stack

1. Open [http://localhost:5173](http://localhost:5173) in your browser.
2. Click **"Get Started"** or **"Sign Up"** and create an account.
3. Navigate to **"Scan Receipt"** and upload a bill (PDF or image).
4. Review extracted items, click **"Save Products"**, and explore your dashboard!

---

## 4. Running the Automated Test Suite

To verify that your installation is 100% functional:
```powershell
cd backend
.venv\Scripts\python -m pytest -v
```
All **82 automated tests** should pass.

---

*OWNIT Setup Guide — Verified for clean installations.*
