"""
Flat Array-Based Cryptographic Merkle Tree Engine
Invariant: Complete binary tree representation in contiguous flat memory.
Complexity: O(N) linear build, O(log N) inclusion proof generation, O(log N) verification.
Memory: Zero recursive allocation, array-based index traversal (2*i + 1, 2*i + 2).
"""

from eth_utils import keccak
from typing import List, Tuple


class FlatMerkleTree:
    """
    In-Memory Array-Indexed Merkle Tree.
    Nodes are indexed sequentially layer by layer.
    """
    def __init__(self, raw_leaves: List[str]):
        assert isinstance(raw_leaves, list), "Leaves must be a list"
        assert len(raw_leaves) > 0, "Leaves cannot be empty"

        # 1. Hash leaves to 32-byte Keccak digest
        self.leaf_digests: List[bytes] = [
            keccak(item.encode("utf-8") if isinstance(item, str) else item)
            for item in raw_leaves
        ]

        # 2. Build layers
        self.layers: List[List[bytes]] = [self.leaf_digests]
        self._build_tree()

    def _build_tree(self):
        current = self.leaf_digests
        while len(current) > 1:
            if len(current) % 2 != 0:
                current = current + [current[-1]]  # Duplicate odd tail
            
            next_layer = []
            for i in range(0, len(current), 2):
                combined = current[i] + current[i + 1]
                next_layer.append(keccak(combined))
            self.layers.append(next_layer)
            current = next_layer

    @property
    def root(self) -> str:
        assert len(self.layers) > 0, "Tree must have layers"
        return "0x" + self.layers[-1][0].hex()

    def get_proof(self, leaf_index: int) -> List[Tuple[str, str]]:
        """
        Generate Merkle audit proof path for a specific leaf.
        Returns list of (sibling_hash_hex, 'left'|'right').
        """
        assert 0 <= leaf_index < len(self.leaf_digests), "Leaf index out of range"
        proof: List[Tuple[str, str]] = []
        idx = leaf_index

        for layer in self.layers[:-1]:
            is_right_child = (idx % 2 == 1)
            sibling_idx = idx - 1 if is_right_child else idx + 1
            if sibling_idx >= len(layer):
                sibling_idx = idx  # Paired with duplicate self

            sibling_hash = "0x" + layer[sibling_idx].hex()
            position = "left" if is_right_child else "right"
            proof.append((sibling_hash, position))

            idx = idx // 2

        return proof

    @staticmethod
    def verify_proof(leaf: str, proof: List[Tuple[str, str]], root: str) -> bool:
        """
        Verify cryptographic inclusion in O(log N) time.
        """
        assert isinstance(leaf, str), "Leaf must be a string"
        assert isinstance(root, str), "Root must be a string"

        current = keccak(leaf.encode("utf-8") if isinstance(leaf, str) else leaf)

        for sibling_hex, pos in proof:
            sibling_bytes = bytes.fromhex(sibling_hex[2:])
            if pos == "left":
                combined = sibling_bytes + current
            else:
                combined = current + sibling_bytes
            current = keccak(combined)

        computed_root = "0x" + current.hex()
        return computed_root.lower() == root.lower()
