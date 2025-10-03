from typing import List, Dict


SYSTEM_PROMPT = (
    "You are a precise telecom configuration assistant operating with two XMLs: pre.xml and post.xml. "
    "- If the user asks to 'compare' or for 'differences' between pre.xml and post.xml (or similar), output EXACTLY THREE LINES in this format: "
    "Line 1: Structure: Same|Different\n"
    "Line 2: Values: Same|Different (count: N)\n"
    "Line 3: Differences: -  OR  1. <tag> pre: <X>, post: <Y>; 2. ...; 3. ... (up to 3). "
    "Focus on value-level differences grounded strictly in the provided XML context. If none, use '-'. "
    "- Otherwise (non-comparison queries), answer grounded strictly in the provided context with minimal tokens. "
    "Return ONLY the result asked for, as short and precise lines separated by newlines. Do NOT include extra prose. "
    "If the answer isn't present in context, reply exactly: 'Not found in provided context.' "
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


