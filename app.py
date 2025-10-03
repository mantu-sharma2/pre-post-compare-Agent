from flask import Flask, render_template, request, jsonify
from typing import List, Dict

from config import HOST, PORT, DEBUG
from api_client import RakutenAIClient
from rag.indexer import RAGIndexer
from rag.retriever import Retriever
from services.comparator import compare_xml
from services.prompt_builder import build_messages, SYSTEM_PROMPT
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
    want_full: bool = bool((payload or {}).get("full", False))
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

    # If the question asks for comparison, compute structured diff locally as grounding
    wants_compare = any(w in user_query.lower() for w in ["compare", "difference", "diff", "different", "change"])
    comparison_html = None
    if wants_compare:
        with open(PRE_XML_FILE_PATH, "r", encoding="utf-8", errors="ignore") as f:
            pre_text = f.read()[:MAX_FULL_CONTEXT_CHARS]
        with open(POST_XML_FILE_PATH, "r", encoding="utf-8", errors="ignore") as f:
            post_text = f.read()[:MAX_FULL_CONTEXT_CHARS]
        comp = compare_xml(pre_text, post_text)
        if "error" in comp:
            comparison_html = f"<p>Comparison error: {comp['error']}</p>"
        else:
            paths_pre = comp.get("only_in_pre_paths", [])
            paths_post = comp.get("only_in_post_paths", [])
            freq = comp.get("frequency_differences", [])
            rows = "".join(
                f"<tr><td>{d['tag']}</td><td>{d['pre']}</td><td>{d['post']}</td></tr>" for d in freq[:20]
            )
            ul_pre = "".join(f"<li>{p}</li>" for p in paths_pre[:20])
            ul_post = "".join(f"<li>{p}</li>" for p in paths_post[:20])
            comparison_html = (
                f"<section><h3>Structure Same?</h3><p>{'Yes' if comp['structure_same'] else 'No'}</p>"
                f"<h3>Totals</h3><p>pre: {comp['total_elements_pre']}, post: {comp['total_elements_post']}</p>"
                f"<h3>Differences</h3>"
                f"<h4>Tag frequency differences (top 20)</h4>"
                f"<table><thead><tr><th>tag</th><th>pre</th><th>post</th></tr></thead><tbody>{rows}</tbody></table>"
                f"<h4>Paths only in pre (top 20)</h4><ul>{ul_pre}</ul>"
                f"<h4>Paths only in post (top 20)</h4><ul>{ul_post}</ul>"
                f"</section>"
            )

    messages: List[Dict[str, str]] = build_messages(context, user_query)

    try:
        answer = client.chat(messages, temperature=0.1, max_tokens=900)
        # If comparison was requested, prepend structured section
        if comparison_html:
            answer_html = f"{comparison_html}<hr><div>{answer}</div>"
        else:
            answer_html = answer
        return jsonify({
            "answer": answer_html,
            "snippets": snippet_ids,
            "structured": bool(comparison_html),
        })
    except requests.exceptions.RequestException as e:
        fallback = (
            "Could not reach the Rakuten AI service right now. "
            "Network/DNS or gateway access may be unavailable. "
            "Here are the most relevant XML snippets for your query; please try again later."
        )
        html = comparison_html or ""
        return jsonify({
            "answer": (html + ("<p>" + fallback + "</p>") if html else fallback),
            "error": str(e),
            "snippets": snippet_ids,
            "structured": bool(comparison_html),
        }), 502
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=DEBUG)


