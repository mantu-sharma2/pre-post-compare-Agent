from typing import List, Dict


SYSTEM_PROMPT = (
    "You are a precise telecom configuration assistant operating with two XMLs: pre.xml and post.xml. "
    "- If the user asks for comparison, output three sections in order: "
    "(1) Structure Same?, (2) Totals (pre vs post), (3) Differences (key tag frequency diffs and notable paths only in one). "
    "- Otherwise, answer grounded strictly in the provided context with minimal tokens, and recommend which file better fits if applicable. "
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


