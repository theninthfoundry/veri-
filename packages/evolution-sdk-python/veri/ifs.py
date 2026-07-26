"""
VERI Intelligence File System (IFS) — BehaviorOS v6.0

Virtual POSIX Filesystem for Autonomous Intelligence.
Instead of files on disk, everything is a versioned Knowledge Object:
  - /sys/behavior/processes/<bid>/state
  - /sys/behavior/goals/<goal_id>
  - /sys/behavior/beliefs/<belief_id>
  - /sys/behavior/decisions/<decision_id>
  - /sys/behavior/genomes/<agent_id>
  - /sys/behavior/policies/<policy_id>

Supports POSIX-like `read()`, `write()`, `stat()`, `ls()`, and object version diffing.
"""

import time
from typing import List, Dict, Any, Optional, Set, Tuple


# ── Knowledge Object ──────────────────────────────────────────────


class KnowledgeObject:
    """A single versioned object in the Intelligence File System."""

    def __init__(
        self,
        path: str,
        object_type: str,
        content: Any,
        version: int = 1,
        author: str = "ikernel",
    ):
        self.path = path
        self.object_type = object_type  # "goal", "belief", "evidence", "decision", "genome", "policy"
        self.content = content
        self.version = version
        self.author = author
        self.created_at = time.time()
        self.updated_at = time.time()

    def update(self, new_content: Any, author: str = "ikernel") -> None:
        self.content = new_content
        self.version += 1
        self.author = author
        self.updated_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "object_type": self.object_type,
            "content": str(self.content),
            "version": self.version,
            "author": self.author,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


# ── Intelligence File System (IFS) ────────────────────────────────


class IntelligenceFileSystem:
    """
    Virtual POSIX VFS for intelligence objects.
    Presents process state, goals, beliefs, genomes, and decisions
    as a searchable, versioned directory tree (`/sys/behavior/...`).
    """

    def __init__(self):
        self.objects: Dict[str, KnowledgeObject] = {}

    def write(
        self,
        path: str,
        content: Any,
        object_type: str = "generic",
        author: str = "ikernel",
    ) -> KnowledgeObject:
        """Writes or updates a Knowledge Object at virtual path."""
        norm_path = self._normalize_path(path)
        if norm_path in self.objects:
            obj = self.objects[norm_path]
            obj.update(content, author)
        else:
            obj = KnowledgeObject(
                path=norm_path,
                object_type=object_type,
                content=content,
                version=1,
                author=author,
            )
            self.objects[norm_path] = obj
        return obj

    def read(self, path: str) -> Optional[KnowledgeObject]:
        """Reads a Knowledge Object from virtual path (cat equivalent)."""
        norm_path = self._normalize_path(path)
        return self.objects.get(norm_path)

    def ls(self, prefix_path: str = "/sys/behavior") -> List[Dict[str, Any]]:
        """Lists directory contents under virtual path (ls equivalent)."""
        norm_prefix = self._normalize_path(prefix_path)
        matched = []

        for p, obj in self.objects.items():
            if p.startswith(norm_prefix):
                matched.append(obj.to_dict())

        return matched

    def stat(self, path: str) -> Optional[Dict[str, Any]]:
        """Returns object metadata (stat equivalent)."""
        obj = self.read(path)
        if not obj:
            return None
        return {
            "path": obj.path,
            "object_type": obj.object_type,
            "version": obj.version,
            "author": obj.author,
            "size_bytes": len(str(obj.content)),
            "created_at": obj.created_at,
            "updated_at": obj.updated_at,
        }

    def _normalize_path(self, path: str) -> str:
        """Normalizes IFS path (ensures /sys/behavior prefix)."""
        p = path.strip()
        if not p.startswith("/"):
            p = "/" + p
        if not p.startswith("/sys/behavior"):
            p = "/sys/behavior" + p
        return p.rstrip("/")
