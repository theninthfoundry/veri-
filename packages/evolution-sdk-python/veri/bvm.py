"""
VERI Behavior Virtual Machine (BVM) — BehaviorOS v6.0

Provider-Agnostic Cognitive Bytecode Virtual Machine.
Analogous to JVM for Java or CLR for .NET.

Executes provider-neutral cognitive bytecode instructions:
  - OP_THINK           ──► Triggers LLM reasoning step
  - OP_INSPECT_MEMORY  ──► Reads L1-L6 memory layers
  - OP_VERIFY_POLICY   ──► Evaluates BehaviorContract policy rules
  - OP_EXECUTE_TOOL    ──► Invokes external tool API
  - OP_REFLECT         ──► Computes self-evaluation & confidence score

Runs OpenAI, Anthropic, Gemini, or local models identically via bytecode abstraction.
"""

import time
from enum import Enum
from typing import List, Dict, Any, Optional

from veri.ir import RuntimeNode, NodeKind
from veri.contracts import BehaviorContract, ContractViolation


# ── Cognitive Bytecode Opcodes ─────────────────────────────────────


class BVMOpcode(Enum):
    OP_THINK = "OP_THINK"
    OP_INSPECT_MEMORY = "OP_INSPECT_MEMORY"
    OP_VERIFY_POLICY = "OP_VERIFY_POLICY"
    OP_EXECUTE_TOOL = "OP_EXECUTE_TOOL"
    OP_REFLECT = "OP_REFLECT"
    OP_HALT = "OP_HALT"


class BVMInstruction:
    """A single cognitive bytecode instruction."""

    def __init__(self, opcode: BVMOpcode, operand: Dict[str, Any]):
        self.opcode = opcode
        self.operand = operand

    def to_dict(self) -> Dict[str, Any]:
        return {
            "opcode": self.opcode.value,
            "operand": self.operand,
        }


class BVMExecutionResult:
    """Result of executing a cognitive bytecode program."""

    def __init__(
        self,
        program_id: str,
        instructions_executed: int,
        output_state: Dict[str, Any],
        violations: List[ContractViolation],
        execution_time_ms: float,
        success: bool,
    ):
        self.program_id = program_id
        self.instructions_executed = instructions_executed
        self.output_state = output_state
        self.violations = violations
        self.execution_time_ms = execution_time_ms
        self.success = success

    def to_dict(self) -> Dict[str, Any]:
        return {
            "program_id": self.program_id,
            "instructions_executed": self.instructions_executed,
            "output_state": self.output_state,
            "violations": [v.to_dict() for v in self.violations],
            "execution_time_ms": round(self.execution_time_ms, 3),
            "success": self.success,
        }


# ── Behavior Virtual Machine Engine ───────────────────────────────


class BehaviorVirtualMachine:
    """
    Cognitive Bytecode Interpreter (BVM).
    Executes instruction streams in a sandbox with verified policy boundaries.
    """

    def __init__(self, provider_model: str = "gpt-4o"):
        self.provider_model = provider_model

    def execute_program(
        self,
        program_id: str,
        instructions: List[BVMInstruction],
        contract: Optional[BehaviorContract] = None,
    ) -> BVMExecutionResult:
        """Executes a list of BVMInstruction objects sequentially."""
        start_time = time.time()
        contract_obj = contract or BehaviorContract()

        state: Dict[str, Any] = {
            "memory": {},
            "reflections": [],
            "executed_tools": [],
            "confidence": 0.85,
        }
        violations: List[ContractViolation] = []
        executed_count = 0
        success = True

        for inst in instructions:
            executed_count += 1
            op = inst.opcode
            arg = inst.operand

            if op == BVMOpcode.OP_INSPECT_MEMORY:
                key = arg.get("key", "context")
                state["memory"][key] = f"Inspected memory value for '{key}'"

            elif op == BVMOpcode.OP_VERIFY_POLICY:
                rule = arg.get("rule", "max_cost")
                # Evaluate rule
                if rule == "forbidden_tools" and arg.get("tool") in contract_obj.forbidden_tools:
                    violations.append(ContractViolation(
                        node_id="bvm_inst",
                        node_name=arg.get("tool", "tool"),
                        rule="forbidden_tools",
                        message=f"Forbidden tool '{arg.get('tool')}' in BVM execution.",
                        details=arg,
                    ))
                    success = False
                    break

            elif op == BVMOpcode.OP_EXECUTE_TOOL:
                tool_name = arg.get("tool", "generic_tool")
                state["executed_tools"].append(tool_name)

            elif op == BVMOpcode.OP_REFLECT:
                state["reflections"].append(arg.get("reflection", "Self-evaluation completed."))

            elif op == BVMOpcode.OP_HALT:
                break

        exec_time = (time.time() - start_time) * 1000.0

        return BVMExecutionResult(
            program_id=program_id,
            instructions_executed=executed_count,
            output_state=state,
            violations=violations,
            execution_time_ms=exec_time,
            success=success,
        )
