# OWNIT
> **"Own More. Worry Less."**

OWNIT is an intelligent **Smart Product Lifecycle Assistant** designed to help users track their purchases, warranties, return windows, service history, and maintenance schedules — powered by OCR receipt scanning and local AI.

---

## 🌟 Overview

Managing physical possessions, invoices, warranty terms, and service dates can be chaotic. OWNIT solves this problem by centralizing everything into a single, intuitive platform:

- 🧾 **Receipt & Invoice Scanning**: Extract product details and dates automatically using Tesseract OCR.
- 🛡️ **Warranty & Return Management**: Track return windows, warranty deadlines, inclusions, and exclusions.
- 🤖 **Local AI Assistant**: Query product-specific manuals and warranty terms powered by a private, local LLM via Ollama.
- 📈 **Product Life Score & Timeline**: Monitor maintenance schedules, health indicators, and service history.
- 🌐 **Multilingual Support**: English, Hindi (हिंदी), and Telugu (తెలుగు).

---

## 🏗️ Repository Architecture

This project is structured as a clean monorepo:

```text
OWNIT/
├── frontend/          # React + Vite web user interface
├── backend/           # FastAPI (Python) REST API service
├── docs/              # Architectural, setup, and roadmap documentation
├── .gitignore         # Rules to ignore build, virtualenv, and secret files
└── README.md          # Project overview and getting started guide
```

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | React, Vite, React Router, Modern CSS | Fast, interactive user interface |
| **Backend** | Python 3.10+, FastAPI, Uvicorn | High-performance asynchronous REST API |
| **Database** | MongoDB | Document store for flexible product & warranty schemas |
| **OCR** | Tesseract OCR | Image-to-text extraction for receipts and warranty cards |
| **AI** | Ollama (Local open-source LLM) | Offline, private conversational assistance and extraction |
| **Auth** | JWT, Secure Password Hashing | User authentication and session security |

---

## 🚀 Getting Started

Detailed step-by-step setup guides can be found in the [docs/](file:///c:/Users/kotha/Documents/projects/OWNIT/docs) directory:

- [docs/development.md](file:///c:/Users/kotha/Documents/projects/OWNIT/docs/development.md) — Local development and environment setup guide.
- [docs/architecture.md](file:///c:/Users/kotha/Documents/projects/OWNIT/docs/architecture.md) — System design and data flow breakdown.
- [docs/roadmap.md](file:///c:/Users/kotha/Documents/projects/OWNIT/docs/roadmap.md) — Step-by-step development roadmap.

### Quick Start Summary

#### 1. Backend (FastAPI)
```powershell
# Navigate to backend
cd backend

# Create and activate a Python virtual environment
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn main:app --reload --port 8000
```
Backend API will be available at: [http://localhost:8000](http://localhost:8000) (Interactive Swagger Docs: [http://localhost:8000/docs](http://localhost:8000/docs))

#### 2. Frontend (React + Vite)
```powershell
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start Vite dev server
npm run dev
```
Frontend Web App will be available at: [http://localhost:5173](http://localhost:5173)

---

## 🔒 Security & Privacy

- All sensitive keys and configuration parameters are loaded via environment variables (`.env`).
- Secrets and temporary receipt uploads are strictly excluded from version control via `.gitignore`.
- AI inference runs **locally** using Ollama without sending personal receipt data to external third-party APIs.
