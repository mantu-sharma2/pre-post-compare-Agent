from typing import List, Dict


SYSTEM_PROMPT = (
    "You are a precise telecom configuration assistant operating with two XMLs: pre.xml and post.xml. "
    "- If the user asks for comparison, output three sections in order: "
    "(1) Structure Same?, (2) Totals (pre vs post), (3) Differences (key tag frequency diffs and notable paths only in one). "
    "- Otherwise (non-comparison queries), answer grounded strictly in the provided context with minimal tokens. "
    "Return ONLY the result asked for, as short and precise lines separated by newlines. "
    "Do NOT include explanations, headers, bullets, or extra prose. If multiple values, list each on its own line. "
    "After the result lines, add one final short line starting with 'Summary:' that briefly comments on the result (≤15 words). "
    "If the answer isn't present in context, reply exactly: 'Not found in provided context.' "
    "When applicable, you may mention which file (pre or post) better fits within the Summary line only. "
    "Use concise, readable formatting; avoid speculation."
)


def build_messages(context: str, user_query: str) -> List[Dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "Use the following context from pre.xml and post.xml. If answer isn't present, say so.\n\n"
                + context
                + "\n\nQuestion: "
                + user_query
            ),
        },
    ]


# General fallback when the answer is outside provided context
SYSTEM_GENERAL = (
    "You are a helpful assistant. Answer the user's question concisely and accurately. "
    "No special formatting is required; respond naturally."
)


def build_general_messages(user_query: str) -> List[Dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_GENERAL},
        {"role": "user", "content": user_query},
    ]


