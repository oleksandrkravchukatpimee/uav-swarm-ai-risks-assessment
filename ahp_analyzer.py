from fractions import Fraction
from typing import Any, Dict, List, Mapping, Tuple

import numpy as np

class AHPAnalyzer:
    STAGE_CHILD_KEYS = ("factors",)
    FACTOR_CHILD_KEYS = ("risks",)
    DEFAULT_CHILD_KEYS = ("risks",)

    @staticmethod
    def load_hierarchy(yaml_file: str) -> Dict[str, Any]:
        import yaml

        with open(yaml_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    @staticmethod
    def _parse_value(value: Any) -> float:
        if isinstance(value, str) and "/" in value:
            return float(Fraction(value))
        return float(value)

    def _comparison_dict(self, compares: Any) -> Dict[str, float]:
        if compares is None:
            return {}

        if isinstance(compares, dict):
            return {str(target): self._parse_value(val) for target, val in compares.items()}

        if isinstance(compares, list):
            normalized: Dict[str, float] = {}
            for entry in compares:
                if isinstance(entry, (list, tuple)) and len(entry) == 2:
                    target, val = entry
                    normalized[str(target)] = self._parse_value(val)
                    continue

                if isinstance(entry, dict) and "target" in entry and "value" in entry:
                    normalized[str(entry["target"])] = self._parse_value(entry["value"])
                    continue

                raise TypeError(f"Unsupported compare entry format: {entry!r}")
            return normalized

        raise TypeError(f"Unsupported compare format: {type(compares).__name__}")

    @staticmethod
    def _normalize_signed_value(signed_val: float) -> float:
        if signed_val == 0:
            return 1.0
        return signed_val if signed_val > 0 else -1 / signed_val

    @staticmethod
    def _set_reciprocal_pair(matrix: np.ndarray, i: int, j: int, val: float) -> None:
        matrix[i][j] = 1 / val
        matrix[j][i] = val

    @staticmethod
    def _label_id(item_id: str, id_to_label: Mapping[str, str] | None) -> str:
        item = str(item_id)
        if id_to_label is None:
            return item
        return str(id_to_label.get(item, item))

    def _child_keys_for_depth(self, depth: int) -> Tuple[str, ...]:
        if depth == 0:
            return self.STAGE_CHILD_KEYS
        if depth == 1:
            return self.FACTOR_CHILD_KEYS
        return self.DEFAULT_CHILD_KEYS

    def _get_children_dict(self, node: Dict[str, Any], depth: int) -> Dict[str, Any]:
        for key in self._child_keys_for_depth(depth):
            children = node.get(key)
            if isinstance(children, dict):
                return children
        return {}

    def _build_root_matrix_block(self, hierarchy: Dict[str, Any]) -> Dict[str, Any]:
        root_items = list(hierarchy.keys())
        root_matrix = np.ones((len(root_items), len(root_items)))

        for i, item_i in enumerate(root_items):
            compares = hierarchy[item_i].get("compare", [])
            compare_dict = self._comparison_dict(compares)
            for j, item_j in enumerate(root_items):
                if item_j in compare_dict:
                    val = self._normalize_signed_value(compare_dict[item_j])
                    self._set_reciprocal_pair(root_matrix, i, j, val)

        return {
            "path": [],
            "items": root_items,
            "matrix": root_matrix,
        }

    def _fill_nested_matrix_cell(
        self,
        matrix: np.ndarray,
        items_dict: Dict[str, Any],
        items: List[str],
        i: int,
        j: int,
        compare_dict: Dict[str, float],
    ) -> None:
        item_i = items[i]
        item_j = items[j]
        if item_j in compare_dict:
            val = self._normalize_signed_value(compare_dict[item_j])
            self._set_reciprocal_pair(matrix, i, j, val)
            return

        compares_j = items_dict[item_j].get("compare", [])
        reverse_dict = self._comparison_dict(compares_j)
        if item_i in reverse_dict:
            val = self._normalize_signed_value(reverse_dict[item_i])
            self._set_reciprocal_pair(matrix, j, i, val)

    def _build_nested_matrix_block(self, items_dict: Dict[str, Any], path: List[str]) -> Dict[str, Any] | None:
        items = list(items_dict.keys())
        if not items:
            return None

        size = len(items)
        matrix = np.ones((size, size))

        for i, item_i in enumerate(items):
            if not isinstance(items_dict[item_i], dict):
                continue
            compares_i = items_dict[item_i].get("compare", [])
            compare_dict = self._comparison_dict(compares_i)
            for j in range(size):
                self._fill_nested_matrix_cell(matrix, items_dict, items, i, j, compare_dict)

        return {
            "path": path,
            "items": items,
            "matrix": matrix,
        }

    def _collect_nested_matrices(self, node: Dict[str, Any], path: List[str] | None = None) -> List[Dict[str, Any]]:
        current_path = path or []
        results: List[Dict[str, Any]] = []

        for key, sub in node.items():
            if not isinstance(sub, dict):
                continue
            nested_path = current_path + [key]
            depth = len(nested_path) - 1
            children_dict = self._get_children_dict(sub, depth)
            if not children_dict:
                continue

            block = self._build_nested_matrix_block(children_dict, nested_path)
            if block is not None:
                results.append(block)
            results.extend(self._collect_nested_matrices(children_dict, nested_path))

        return results

    def build_comparison_matrices(self, hierarchy: Dict[str, Any]) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = [self._build_root_matrix_block(hierarchy)]
        results.extend(self._collect_nested_matrices(hierarchy))
        return results

    @staticmethod
    def calculate_ahp(matrix: np.ndarray) -> Tuple[np.ndarray, float, float, float]:
        eigvals, eigvecs = np.linalg.eig(matrix)
        max_index = np.argmax(eigvals.real)
        max_eigval = eigvals.real[max_index]
        weights = eigvecs[:, max_index].real
        weights = weights / np.sum(weights)
        n = matrix.shape[0]
        ci = (max_eigval - n) / (n - 1) if n > 1 else 0.0
        ri = {
            1: 0.0,
            2: 0.0,
            3: 0.58,
            4: 0.90,
            5: 1.12,
            6: 1.24,
            7: 1.32,
            8: 1.41,
            9: 1.45,
            10: 1.49,
        }.get(n, 1.49)
        cr = ci / ri if ri else 0.0
        return weights, max_eigval, ci, cr

    def calculate_local_weights_by_path(
        self,
        flat_data: List[Dict[str, Any]],
        id_to_label: Mapping[str, str] | None = None,
    ) -> Dict[str, Dict[str, Any]]:
        local_weights_by_path: Dict[str, Dict[str, Any]] = {}
        for block in flat_data:
            weights, lam_max, ci, cr = self.calculate_ahp(block["matrix"])
            key_path = " / ".join(self._label_id(path_item, id_to_label) for path_item in block["path"])
            labeled_items = [self._label_id(item, id_to_label) for item in block["items"]]
            local_weights_by_path[key_path] = {
                "items": labeled_items,
                "matrix": block["matrix"],
                "weights": weights,
                "lam_max": lam_max,
                "ci": ci,
                "cr": cr,
            }
        return local_weights_by_path

    @staticmethod
    def propagate_global_weights(local_weights_by_path: Dict[str, Any]) -> Dict[str, float]:
        global_weights: Dict[str, float] = {}
        root_path = ""
        if root_path not in local_weights_by_path:
            raise Exception("Pairwise comparison matrix is absent for stages")

        root_items = local_weights_by_path[root_path]["items"]
        root_weights = local_weights_by_path[root_path]["weights"]

        def recurse(path: List[str], weight: float):
            joined = " / ".join(path)
            if joined in local_weights_by_path:
                items = local_weights_by_path[joined]["items"]
                weights = local_weights_by_path[joined]["weights"]
                for item, local_weight in zip(items, weights):
                    recurse(path + [item], weight * local_weight)
            else:
                global_weights[" / ".join(path)] = weight

        for root, weight in zip(root_items, root_weights):
            recurse([root], weight)

        return global_weights
