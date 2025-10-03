from typing import List, Tuple, Dict, Any
import re
import xml.etree.ElementTree as ET

from config import (
    XML_FILE_PATH,
    PRE_XML_FILE_PATH,
    POST_XML_FILE_PATH,
    MAX_SNIPPETS,
    MAX_TOKENS_PER_SNIPPET,
)


def read_file_text(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def split_xml_into_chunks(xml_text: str, max_chars: int) -> List[str]:
    # Simple chunking by closing tag boundaries to keep context coherent
    chunks: List[str] = []
    current: List[str] = []
    size = 0
    for line in xml_text.splitlines():
        current.append(line)
        size += len(line) + 1
        if size >= max_chars and line.strip().endswith('>'):
            chunks.append("\n".join(current))
            current = []
            size = 0
    if current:
        chunks.append("\n".join(current))
    return chunks


def score_chunk(query: str, chunk: str) -> int:
    # Basic lexical scoring with term frequency; give slight boost to exact uppercase tag hits
    score = 0
    for token in re.findall(r"[A-Za-z0-9_\-]+", query.lower()):
        score += chunk.lower().count(token)
    # Boost for known identifiers like pci, tac, earfcn, enbId
    important = ["pci", "tac", "earfcn", "enbid", "radio", "nb", "nr", "band", "downlink", "uplink"]
    for key in important:
        if key in query.lower():
            score += chunk.lower().count(key) * 2
    return score


def retrieve_relevant_snippets(query: str, k: int = MAX_SNIPPETS) -> List[Tuple[int, str]]:
    xml_text = read_file_text(XML_FILE_PATH)
    chunks = split_xml_into_chunks(xml_text, MAX_TOKENS_PER_SNIPPET)
    scored = [(idx, score_chunk(query, c), c) for idx, c in enumerate(chunks)]
    scored.sort(key=lambda x: x[1], reverse=True)
    top = [(idx, c) for idx, _, c in scored[:k] if _ > 0]
    return top


def retrieve_relevant_snippets_dual(query: str, k: int = MAX_SNIPPETS) -> List[Tuple[str, int, str]]:
    """Return top snippets from pre.xml and post.xml combined with a source label."""
    pre_text = read_file_text(PRE_XML_FILE_PATH)
    post_text = read_file_text(POST_XML_FILE_PATH)
    pre_chunks = split_xml_into_chunks(pre_text, MAX_TOKENS_PER_SNIPPET)
    post_chunks = split_xml_into_chunks(post_text, MAX_TOKENS_PER_SNIPPET)

    scored: List[Tuple[str, int, int, str]] = []
    for idx, c in enumerate(pre_chunks):
        scored.append(("pre", idx, score_chunk(query, c), c))
    for idx, c in enumerate(post_chunks):
        scored.append(("post", idx, score_chunk(query, c), c))
    scored.sort(key=lambda x: x[2], reverse=True)
    top = [(src, idx, c) for src, idx, _, c in scored[:k] if _ > 0]
    return top


def _iter_paths(root: ET.Element) -> List[str]:
    paths: List[str] = []
    def walk(node: ET.Element, path: List[str]):
        tag_name = node.tag.split('}')[-1] if '}' in node.tag else node.tag
        cur = path + [tag_name]
        paths.append('/'.join(cur))
        for child in list(node):
            walk(child, cur)
    walk(root, [])
    return paths


def _tag_counts(root: ET.Element) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for elem in root.iter():
        tag_name = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
        counts[tag_name] = counts.get(tag_name, 0) + 1
    return counts


def compare_xml(pre_text: str, post_text: str) -> Dict[str, Any]:
    """Lightweight comparison: structure and counts, plus differing tags by frequency.
    """
    try:
        pre_root = ET.fromstring(pre_text)
        post_root = ET.fromstring(post_text)
    except Exception as e:
        return {"error": f"Failed to parse XML: {e}"}

    pre_paths = set(_iter_paths(pre_root))
    post_paths = set(_iter_paths(post_root))

    structure_same = pre_paths == post_paths
    only_in_pre = sorted(list(pre_paths - post_paths))[:50]
    only_in_post = sorted(list(post_paths - pre_paths))[:50]

    pre_counts = _tag_counts(pre_root)
    post_counts = _tag_counts(post_root)
    all_tags = sorted(set(pre_counts) | set(post_counts))
    freq_diffs = []
    for t in all_tags:
        a = pre_counts.get(t, 0)
        b = post_counts.get(t, 0)
        if a != b:
            freq_diffs.append({"tag": t, "pre": a, "post": b})

    return {
        "structure_same": structure_same,
        "total_elements_pre": sum(pre_counts.values()),
        "total_elements_post": sum(post_counts.values()),
        "only_in_pre_paths": only_in_pre,
        "only_in_post_paths": only_in_post,
        "frequency_differences": freq_diffs[:100],
    }



