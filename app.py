from flask import Flask, render_template, request, jsonify
from typing import List, Dict

from config import HOST, PORT, DEBUG
from api_client import RakutenAIClient
from rag.indexer import RAGIndexer
from rag.retriever import Retriever
from services.prompt_builder import build_messages, build_general_messages, SYSTEM_PROMPT
from config import PRE_XML_FILE_PATH, POST_XML_FILE_PATH, MAX_FULL_CONTEXT_CHARS, MAX_TOKENS_PER_SNIPPET, MAX_SNIPPETS
import requests


app = Flask(__name__)
client = RakutenAIClient()
indexer = RAGIndexer(max_chars_per_chunk=MAX_TOKENS_PER_SNIPPET)
indexer.build(PRE_XML_FILE_PATH, POST_XML_FILE_PATH)
retriever = Retriever(indexer)




@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/chat")
def chat_api():
    payload = request.get_json(force=True)
    user_query: str = (payload or {}).get("query", "").strip()
    want_full: bool = True
    if not user_query:
        return jsonify({"error": "query is required"}), 400

    # Dual retrieval from pre and post
    # Build context: snippets via retriever or full files
    if want_full:
        with open(PRE_XML_FILE_PATH, "r", encoding="utf-8", errors="ignore") as f:
            pre_text = f.read()[:MAX_FULL_CONTEXT_CHARS]
        with open(POST_XML_FILE_PATH, "r", encoding="utf-8", errors="ignore") as f:
            post_text = f.read()[:MAX_FULL_CONTEXT_CHARS]
        context = f"[PRE.xml]\n{pre_text}\n\n[POST.xml]\n{post_text}"
        snippet_ids = []
    else:
        retrieved = retriever.retrieve(user_query, k=MAX_SNIPPETS)
        context = retrieved.formatted or "(No relevant snippets found in pre/post)"
        snippet_ids = retrieved.ids

    # Let the model handle comparison formatting per the system prompt

    messages: List[Dict[str, str]] = build_messages(context, user_query)

    try:
        answer = client.chat(messages, temperature=0.1, max_tokens=900)
        # If the model indicates the answer is not in context, try a general fallback
        if answer.strip().lower().startswith("not found in provided context"):
            general_messages = build_general_messages(user_query)
            answer = client.chat(general_messages, temperature=0.3, max_tokens=900)
        answer_html = answer
        return jsonify({
            "answer": answer_html,
            "snippets": snippet_ids,
            "structured": False,
        })
    except requests.exceptions.RequestException as e:
        fallback = (
            "Could not reach the Rakuten AI service right now. "
            "Network/DNS or gateway access may be unavailable. "
            "Here are the most relevant XML snippets for your query; please try again later."
        )
        return jsonify({
            "answer": fallback,
            "error": str(e),
            "snippets": snippet_ids,
            "structured": False,
        }), 502
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=DEBUG)


