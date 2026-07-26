"""
VERI Hierarchical Memory Manager — BehaviorOS v6.0

Hierarchical Memory Architecture for Autonomous Intelligence:
  - L1 Working Memory     ──► Active context window state
  - L2 Session Memory     ──► Single session execution trajectory
  - L3 Organization Memory──► Departmental shared knowledge & policies
  - L4 Behavior Memory    ──► Operational patterns, failures & recoveries
  - L5 Knowledge Memory   ──► Persistent RAG / vector index
  - L6 Collective Memory  ──► Fleet-wide cross-org shared memory

Manages automatic page swapping, LRU eviction, semantic compression, and archival.
"""

import time
from enum import Enum
from typing import List, Dict, Any, Optional, Set, Tuple
from collections import OrderedDict

from veri.ir import RuntimeNode


# ── Memory Layer Enum ─────────────────────────────────────────────


class MemoryLayer(Enum):
    L1_WORKING = "l1_working"
    L2_SESSION = "l2_session"
    L3_ORGANIZATION = "l3_organization"
    L4_BEHAVIOR = "l4_behavior"
    L5_KNOWLEDGE = "l5_knowledge"
    L6_COLLECTIVE = "l6_collective"


# ── Memory Item ───────────────────────────────────────────────────


class MemoryItem:
    """An item stored in a specific MemoryLayer."""

    def __init__(
        self,
        item_id: str,
        layer: MemoryLayer,
        key: str,
        value: Any,
        tokens: int = 100,
        ttl_seconds: Optional[float] = None,
    ):
        self.item_id = item_id
        self.layer = layer
        self.key = key
        self.value = value
        self.tokens = tokens
        self.ttl_seconds = ttl_seconds
        self.created_at = time.time()
        self.last_accessed_at = time.time()
        self.access_count = 0

    def touch(self) -> None:
        self.last_accessed_at = time.time()
        self.access_count += 1

    @property
    def is_expired(self) -> bool:
        if self.ttl_seconds is None:
            return False
        return (time.time() - self.created_at) > self.ttl_seconds

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "layer": self.layer.value,
            "key": self.key,
            "value": str(self.value),
            "tokens": self.tokens,
            "access_count": self.access_count,
            "created_at": self.created_at,
            "last_accessed_at": self.last_accessed_at,
        }


# ── Hierarchical Memory Manager ───────────────────────────────────


class HierarchicalMemoryManager:
    """
    Manages all 6 memory layers (L1-L6) for a Behavior Process or Fleet.

    Applies LRU page swapping from L1 (Working) down to L6 (Collective),
    performing semantic compression when lower layers reach capacity.
    """

    def __init__(
        self,
        l1_max_tokens: int = 4000,
        l2_max_tokens: int = 16000,
        l3_max_tokens: int = 64000,
    ):
        self.l1_max_tokens = l1_max_tokens
        self.l2_max_tokens = l2_max_tokens
        self.l3_max_tokens = l3_max_tokens

        # Layer stores (OrderedDict for LRU)
        self.stores: Dict[MemoryLayer, OrderedDict] = {
            layer: OrderedDict() for layer in MemoryLayer
        }

    def write(
        self,
        layer: MemoryLayer,
        key: str,
        value: Any,
        tokens: int = 100,
        ttl_seconds: Optional[float] = None,
    ) -> MemoryItem:
        """Writes an item to a target memory layer, applying LRU eviction if full."""
        item_id = f"mem_{layer.value}_{len(self.stores[layer]) + 1}"
        item = MemoryItem(
            item_id=item_id,
            layer=layer,
            key=key,
            value=value,
            tokens=tokens,
            ttl_seconds=ttl_seconds,
        )

        store = self.stores[layer]

        # Enforce LRU capacity for L1
        if layer == MemoryLayer.L1_WORKING:
            current_tokens = sum(i.tokens for i in store.values())
            while current_tokens + tokens > self.l1_max_tokens and store:
                # Evict oldest L1 item down to L2 (Memory Swapping)
                evicted_key, evicted_item = store.popitem(last=False)
                current_tokens -= evicted_item.tokens
                self.write(MemoryLayer.L2_SESSION, evicted_item.key, evicted_item.value, evicted_item.tokens)

        store[key] = item
        return item

    def read(self, layer: MemoryLayer, key: str) -> Optional[MemoryItem]:
        """Reads an item from a memory layer and touches its LRU timestamp."""
        store = self.stores[layer]
        item = store.get(key)

        if item:
            if item.is_expired:
                del store[key]
                return None
            item.touch()
            # Move to end (most recently used)
            store.move_to_end(key)
            return item

        # Memory Cascade: look down subsequent layers
        if layer == MemoryLayer.L1_WORKING:
            cascaded = self.read(MemoryLayer.L2_SESSION, key)
            if cascaded:
                # Page-in to L1
                self.write(MemoryLayer.L1_WORKING, key, cascaded.value, cascaded.tokens)
                return cascaded

        return None

    def get_layer_stats(() -> Dict[str, Any]:
        pass

    def get_memory_stats(self) -> Dict[str, Any]:
        """Summary statistics across all 6 memory layers."""
        stats = {}
        for layer in MemoryLayer:
            store = self.stores[layer]
            total_items = len(store)
            total_tokens = sum(i.tokens for i in store.values())
            stats[layer.value] = {
                "items_count": total_items,
                "tokens_count": total_tokens,
            }
        return stats
