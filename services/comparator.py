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

    # Collect value-level differences for nodes that exist in both trees along the same paths
    def _collect_leaf_values(root: ET.Element) -> Dict[str, List[str]]:
        values: Dict[str, List[str]] = {}
        def walk(node: ET.Element, path: List[str]):
            tag_name = node.tag.split('}')[-1] if '}' in node.tag else node.tag
            cur_path = path + [tag_name]
            children = list(node)
            # Build a simple value signature: attributes + text content (trimmed)
            attrs = " ".join(f"{k}={v}" for k, v in sorted(node.attrib.items()))
            text = (node.text or "").strip()
            value_sig = (attrs + "|" + text).strip("|")
            if not children:
                key = '/'.join(cur_path)
                values.setdefault(key, []).append(value_sig)
            for child in children:
                walk(child, cur_path)
        walk(root, [])
        return values

    pre_value_map = _collect_leaf_values(pre_root)
    post_value_map = _collect_leaf_values(post_root)

    value_differences: List[Dict[str, Any]] = []
    for path in sorted(set(pre_value_map.keys()) & set(post_value_map.keys())):
        pre_list = pre_value_map[path]
        post_list = post_value_map[path]
        n = min(len(pre_list), len(post_list))
        for i in range(n):
            if pre_list[i] != post_list[i]:
                # Last tag name is the most informative label
                tag = path.split('/')[-1]
                value_differences.append({
                    "tag": tag,
                    "path": path,
                    "pre": pre_list[i],
                    "post": post_list[i],
                })
                if len(value_differences) >= 200:
                    break
        if len(value_differences) >= 200:
            break

    return {
        "structure_same": structure_same,
        "total_elements_pre": sum(pre_counts.values()),
        "total_elements_post": sum(post_counts.values()),
        "only_in_pre_paths": only_in_pre,
        "only_in_post_paths": only_in_post,
        "frequency_differences": freq_diffs[:100],
        "value_differences": value_differences[:200],
    }


