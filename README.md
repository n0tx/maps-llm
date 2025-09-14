# Maps LLM

**Demo: Open WebUI (Gemma:2B) + Google Maps API for finding places**

A lightweight demo project integrating a local LLM (Open WebUI with Gemma:2B) and the Google Maps API to answer queries like "where to find places to go, eat, etc."

---

<img width="978" height="761" alt="image" src="https://github.com/user-attachments/assets/42fa4652-d3f1-408d-95d6-18f9b26b9cb8" />

## Features
- **Frontend**: Simple HTML form served by Flask.
- **Backend**: Flask app handling queries, optional LLM parsing, Google Places API calls, and map embed generation.
- **LLM**: Gemma:2B served locally via Open WebUI for query normalization.
- **APIs**: Google Places Text Search API and Maps Embed API.

## Prerequisites
- Curl
- Docker  
- Ollama CLI  
- Python 3.9+  

## Setup

### 1. Install LLM Locally

- **Install Ollama**

  ```bash
  curl -fsSL https://ollama.com/install.sh | sh
  ```

- **Ollama get Gemma:2b Model**

  ```bash
  ollama pull gemma:2b
  ```

- **Check Ollama Status**

  ```bash
  systemctl status ollama
  ```

### 2. Run Open WebUI

- **Get Open WebUI Image**

  ```bash
  docker pull ghcr.io/open-webui/open-webui:main
  ```

- **Run Open WebUI Image**

  ```bash
  docker run -d --network=host \
    -v open-webui:/app/backend/data \
    -e OLLAMA_BASE_URL=http://127.0.0.1:11434 \
    --name open-webui \
    --restart always \
    ghcr.io/open-webui/open-webui:main
  ```

- **Check Open WebUI**

  ```bash
  http://localhost:8080
  ```

<img width="1432" height="797" alt="image" src="https://github.com/user-attachments/assets/99f07397-0b66-4a94-9476-4887e1ee39f9" />

### 3. Run Flask app

  ```bash
  cd maps-llm
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  cp .env.example .env   # then edit with your API keys
  .venv/bin/python app.py
  ```

- **Check Application**

  ```bash
  http://localhost:5000
  ```

<img width="1008" height="516" alt="image" src="https://github.com/user-attachments/assets/668c74b2-558a-44da-92d8-8c2100cf1722" />

## Environment Variables

See .env.example:
```env
OPENWEBUI_URL=http://localhost:8080
OPENWEBUI_API_KEY=YOUR_OPENWEBUI_API_KEY
GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY
PORT=5000
```

## Example Usage

### Using Browser

```bash
http://localhost:5000
```

### Using Curl

```bash
curl -sS -X POST "http://localhost:5000/search" \
-H "Content-Type: application/json" \
-d '{"query":"Find good ramen in Jakarta", "use_llm": true}' | jq .
```

<img width="1439" height="519" alt="image" src="https://github.com/user-attachments/assets/2c12c143-f90a-4f6f-b376-9b6fb7f76976" />

