from typing import Any, Dict


class PlantUMLExporter:
    def __init__(self, hierarchy: Dict[str, Any], global_weights: Dict[str, float]):
        self.hierarchy = hierarchy
        self.global_weights = global_weights

    def generate(self, output_path: str):
        lines = ["@startmindmap", "* AHP Risk Hierarchy"]

        def get_children_dict(node, depth):
            if not isinstance(node, dict):
                return None

            if depth == 0:
                keys = ("factors",)
            elif depth == 1:
                keys = ("risks",)
            else:
                keys = ("risks",)

            for key in keys:
                children = node.get(key)
                if isinstance(children, dict):
                    return children
            return None

        def add_nodes(node, path=None):
            current_path = path or []
            for key, sub in node.items():
                full_path = current_path + [key]
                line = "*" * (len(full_path) + 1)
                label = key
                joined_path = " / ".join(full_path)
                if joined_path in self.global_weights:
                    label += f" ({self.global_weights[joined_path]:.4f})"
                lines.append(f"{line} {label}")
                children = get_children_dict(sub, len(full_path) - 1)
                if children:
                    add_nodes(children, full_path)

        add_nodes(self.hierarchy)
        lines.append("@endmindmap")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
