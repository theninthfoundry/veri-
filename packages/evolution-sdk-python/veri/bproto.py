"""
VERI Behavior Protocol (BPROTO) — BehaviorOS v6.0

Cognitive Inter-Process Communication (IPC) Protocol for autonomous agents.
Replaces generic HTTP/REST calls with a structured 6-step cognitive negotiation stack:

  1. REQUEST_GOAL  ──► Sender proposes a goal to target process
  2. NEGOTIATE     ──► Processes negotiate resource & constraint bounds
  3. PLAN          ──► Target generates candidate plan
  4. VERIFY        ──► Sender & VERI Kernel verify plan policy compliance
  5. COMMIT        ──► Target commits plan to execution queue
  6. LEARN         ──► Both processes exchange outcome feedback
"""

import time
from enum import Enum
from typing import List, Dict, Any, Optional, Callable


# ── BPROTO Message Type Enum ───────────────────────────────────────


class BProtoMessageType(Enum):
    REQUEST_GOAL = "REQUEST_GOAL"
    NEGOTIATE = "NEGOTIATE"
    PLAN = "PLAN"
    VERIFY = "VERIFY"
    COMMIT = "COMMIT"
    LEARN = "LEARN"


# ── BPROTO Packet ─────────────────────────────────────────────────


class BProtoPacket:
    """A single packet transmitted over the Behavior Protocol."""

    def __init__(
        self,
        sender_bid: str,
        target_bid: str,
        msg_type: BProtoMessageType,
        payload: Dict[str, Any],
        packet_id: Optional[str] = None,
    ):
        self.packet_id = packet_id or f"bproto_{int(time.time()*1000)}"
        self.sender_bid = sender_bid
        self.target_bid = target_bid
        self.msg_type = msg_type
        self.payload = payload
        self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "packet_id": self.packet_id,
            "sender_bid": self.sender_bid,
            "target_bid": self.target_bid,
            "msg_type": self.msg_type.value,
            "payload": self.payload,
            "timestamp": self.timestamp,
        }


# ── BPROTO Session Handler ────────────────────────────────────────


class BProtoSession:
    """
    Manages a 6-step cognitive IPC negotiation between two BehaviorProcesses.
    """

    def __init__(self, session_id: str, sender_bid: str, target_bid: str):
        self.session_id = session_id
        self.sender_bid = sender_bid
        self.target_bid = target_bid
        self.packets: List[BProtoPacket] = []
        self.current_stage = BProtoMessageType.REQUEST_GOAL
        self.committed = False

    def send_packet(
        self, sender_bid: str, msg_type: BProtoMessageType, payload: Dict[str, Any]
    ) -> BProtoPacket:
        """Sends a BPROTO packet and advances the protocol state machine."""
        target_bid = self.target_bid if sender_bid == self.sender_bid else self.sender_bid
        packet = BProtoPacket(
            sender_bid=sender_bid,
            target_bid=target_bid,
            msg_type=msg_type,
            payload=payload,
        )
        self.packets.append(packet)
        self.current_stage = msg_type

        if msg_type == BProtoMessageType.COMMIT:
            self.committed = True

        return packet

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "sender_bid": self.sender_bid,
            "target_bid": self.target_bid,
            "current_stage": self.current_stage.value,
            "committed": self.committed,
            "packets_count": len(self.packets),
            "trace": [p.to_dict() for p in self.packets],
        }
