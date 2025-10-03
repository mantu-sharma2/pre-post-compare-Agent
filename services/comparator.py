from typing import Dict, Any, List
import xml.etree.ElementTree as ET


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


