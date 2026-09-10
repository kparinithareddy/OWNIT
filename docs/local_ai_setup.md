# Local AI Setup & Integration Guide (Ollama)

This guide documents how **OWNIT** ("Own More. Worry Less.") integrates with local AI models using **Ollama** for 100% private, on-device intelligence without any paid cloud APIs or telemetry.

---

## 1. How to Install Ollama

Ollama is a lightweight, open-source tool for running large language models locally on your machine.

### Windows
1. Download the installer from the official website: [ollama.com/download/windows](https://ollama.com/download/windows)
2. Run `OllamaSetup.exe` and complete the installation wizard.
3. Once installed, Ollama runs automatically in the system tray and starts a local server on port `11434` (`http://localhost:11434`).

### macOS
1. Download the `.zip` from [ollama.com/download/mac](https://ollama.com/download/mac) or install via Homebrew:
   ```bash
   brew install ollama
   ```
2. Launch the Ollama application.

### Linux
Run the official install script in your terminal:
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

---

## 2. How to Pull a Suitable Open-Source Model

OWNIT is optimized for lightweight, high-performance instruction-tuned models. We recommend:

- **`llama3.2` (Default Recommended)**: 3B parameters (~2.0 GB). Fast, excellent reasoning for consumer warranty terms and maintenance advice.
- **`mistral`**: 7B parameters (~4.1 GB). Great general-purpose instruction model.
- **`qwen2.5`**: 3B or 7B parameters. High multilingual and structured parsing capabilities.
- **`phi3`**: 3.8B parameters (~2.2 GB). Compact, low memory footprint.

To pull your chosen model, open a terminal / command prompt and run:
```bash
# Pull default recommended model
ollama pull llama3.2

# Or pull an alternative
ollama pull mistral
```

---

## 3. How to Verify the Model

### Step A: Verify via Ollama CLI
List installed models:
```bash
ollama list
```
*Expected Output:*
```text
NAME               ID              SIZE      MODIFIED
llama3.2:latest    a80c4f17acd5    2.0 GB    3 weeks ago
```

Test interactive chat in CLI:
```bash
ollama run llama3.2 "Explain consumer warranty in 1 sentence."
```

### Step B: Verify via REST API
Test Ollama's local HTTP API endpoint:
```bash
curl http://localhost:11434/api/tags
```

---

## 4. How OWNIT Communicates with Ollama

### Architecture & Security Design
- **Zero Browser Exposure**: The client frontend never communicates directly with Ollama (`localhost:11434`).
- **Backend Service Abstraction**: All requests flow securely through `BaseAIService` -> `OllamaAIService` (`backend/app/services/ai_service.py`).
- **Configurable Settings**: Configured via `.env` environment variables without hard-coded models:
  ```ini
  OLLAMA_BASE_URL=http://localhost:11434
  OLLAMA_MODEL=llama3.2
  OLLAMA_TIMEOUT_SECONDS=30.0
  ```
- **Graceful Error Handling & Fallback**:
  - If Ollama is offline or not installed, the application **does not crash**.
  - Standard features (CRUD, Product Life Score, Warranties, Timeline, OCR) remain 100% operational.
  - Endpoints return structured status (`isAvailable: false`, clear reason).

---

## 5. OWNIT Local AI Endpoints

The backend provides the following endpoints under `/api/v1/ai`:

### 1. Check AI Status & Health
- **Endpoint**: `GET /api/v1/ai/status`
- **Authentication**: JWT Bearer Token
- **Sample Response**:
  ```json
  {
    "isAvailable": true,
    "provider": "Ollama",
    "configuredModel": "llama3.2",
    "availableModels": ["llama3.2:latest", "llama2:latest"],
    "baseUrl": "http://localhost:11434",
    "message": "Ollama is running locally. Configured model 'llama3.2' is ready.",
    "error": null
  }
  ```

### 2. Test AI Connectivity & Generation
- **Endpoint**: `POST /api/v1/ai/test`
- **Authentication**: JWT Bearer Token
- **Request Body**:
  ```json
  {
    "prompt": "What are 3 essential maintenance tips for a refrigerator?",
    "systemPrompt": "You are OWNIT Assistant, an expert on home appliances and warranties.",
    "temperature": 0.7
  }
  ```
- **Sample Response**:
  ```json
  {
    "success": true,
    "provider": "Ollama",
    "model": "llama3.2",
    "response": "1. Clean condenser coils every 6 months to prevent motor strain.\n2. Inspect and wipe door gaskets for an airtight seal.\n3. Replace water filters periodically according to manufacturer guidance.",
    "durationMs": 850.4,
    "error": null
  }
  ```
