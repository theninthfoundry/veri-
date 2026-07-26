"""
VERI Behavior Containers & Package Manager (bpkg) — BehaviorOS v6.0

Docker equivalent for AI agents.
Packages agents into portable, versioned `.bcontainer` deployment bundles:
  - Behavior Graph & Trajectory
  - L1-L6 Memory Indexes
  - BehaviorContract Control Policies
  - Goals & Sub-goal Templates
  - Security Permissions & Roles
  - Behavioral Genome & Benchmark Certifications

Enables `veri install finance-agent` or `veri run finance-agent:v4.2`.
"""

import json
import time
from typing import List, Dict, Any, Optional

from veri.contracts import BehaviorContract
from veri.genome import BehaviorGenome


# ── Behavior Container ────────────────────────────────────────────


class BehaviorContainer:
    """
    A portable, versioned `.bcontainer` deployment bundle (Docker image equivalent for AI).
    """

    def __init__(
        self,
        name: str,
        version: str,
        description: str,
        genome: BehaviorGenome,
        contract: BehaviorContract,
        capabilities: List[str],
        author: str = "VERI Registry",
    ):
        self.name = name
        self.version = version
        self.description = description
        self.genome = genome
        self.contract = contract
        self.capabilities = capabilities
        self.author = author
        self.created_at = time.time()

    def serialize_bcontainer(self) -> str:
        """Serializes the container into a `.bcontainer` JSON bundle string."""
        bundle = {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "capabilities": self.capabilities,
            "genome": self.genome.to_dict(),
            "contract": {
                "max_cost": self.contract.max_cost,
                "forbidden_tools": self.contract.forbidden_tools,
                "required_explanations": self.contract.required_explanations,
            },
            "created_at": self.created_at,
        }
        return json.dumps(bundle, indent=2)

    @classmethod
    def deserialize_bcontainer(cls, json_str: str) -> "BehaviorContainer":
        """Deserializes a `.bcontainer` JSON bundle string into a BehaviorContainer."""
        data = json.loads(json_str)
        genome = BehaviorGenome(data.get("genome", {}).get("traits", {}))
        contract_data = data.get("contract", {})
        contract = BehaviorContract(
            max_cost=contract_data.get("max_cost"),
            forbidden_tools=contract_data.get("forbidden_tools"),
            required_explanations=contract_data.get("required_explanations"),
        )
        return cls(
            name=data["name"],
            version=data["version"],
            description=data["description"],
            genome=genome,
            contract=contract,
            capabilities=data.get("capabilities", []),
            author=data.get("author", "unknown"),
        )


# ── Behavior Package Manager (bpkg) ───────────────────────────────


class BehaviorPackageManager:
    """
    Package manager (`bpkg`) for installing and running Behavior Containers.
    Analogue to `npm` or `docker pull`.
    """

    def __init__(self):
        self.installed_packages: Dict[str, BehaviorContainer] = {}

    def install(self, container: BehaviorContainer) -> str:
        """Installs a container into the local behavior store."""
        key = f"{container.name}:{container.version}"
        self.installed_packages[key] = container
        return key

    def get_installed(self, name_with_version: str) -> Optional[BehaviorContainer]:
        return self.installed_packages.get(name_with_version)

    def list_installed(self) -> List[Dict[str, Any]]:
        return [
            {
                "key": key,
                "name": c.name,
                "version": c.version,
                "capabilities": c.capabilities,
                "phenotype": c.genome.to_dict().get("phenotype"),
            }
            for key, c in self.installed_packages.items()
        ]
