# XML Chatbot (Flask + Rakuten AI Gateway)

## Setup

1. Python 3.10+
2. Create venv and install deps:

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. Run:

```
export FLASK_APP=app.py
python app.py
```

Open `http://127.0.0.1:8000`.

## Configuration

- API base URL, key, model are in `config.py`. You can also override via env vars:

  - `RAKUTEN_AI_BASE_URL`
  - `RAKUTEN_AI_GATEWAY_KEY`
  - `RAKUTEN_AI_MODEL`

- Retrieval reads `hemant.xml` by default. Adjust chunking in `config.py` if needed.

## Notes

- The API client calls an OpenAI-compatible `/chat/completions` endpoint with the provided gateway key.
- The assistant is instructed to only answer from XML context; it will say if info is missing.
