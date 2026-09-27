"""
reply_engine.py - Adversarially ordered reply state machine.
Prevents:
- Hostile escalation (handled first -> end)
- Intent-handoff failure (handled second before auto-reply -> send)
- Auto-reply pollution (handled third -> wait or end after repetition)
- Off-topic curveballs (handled fourth -> grounded answer + single CTA)
"""
import re
from typing import Dict, Any, List

class ReplyEngine:
    HOSTILE_PATTERNS = [
        r"\b(stop|unsubscribe|don'?t message|do not (call|message|text|contact)|remove (my|me)|not interested|leave me alone|quit|opt[\s-]?out|cancel messages|spam)\b",
        r"\b(never message|delete my number|harassment|block)\b",
    ]

    # Intent confirmation patterns (checked BEFORE auto-reply)
    INTENT_PATTERNS = [
        r"\b(yes|sure|let'?s proceed|go ahead|activate|confirm|do it|agree|proceed|start it|launch|thumbs up|sounds good|approved|ok proceed|let us proceed)\b",
        r"\b(haan|karein|kar do|chalu karo)\b",
    ]

    AUTO_REPLY_PATTERNS = [
        r"thank you for (contacting|reaching out|messaging)",
        r"we (are|will be) (currently )?(unavailable|away|closed|out of office)",
        r"we will get back to you",
        r"automatic reply",
        r"auto-reply",
        r"auto-generated",
        r"this is an automated response",
        r"do not reply to this email",
    ]

    def _matches_any(self, text: str, patterns: list) -> bool:
        lowered = text.lower()
        for pat in patterns:
            if re.search(pat, lowered):
                return True
        return False

    def process_reply(self, merchant_id: str, message: str, history: List[Dict[str, str]] = None, merchant_name: str = "Partner") -> Dict[str, Any]:
        history = history or []
        msg_clean = message.strip()

        # -------------------------------------------------------------
        # PASS 2 FIX: Stage 1 - Check Hostile / Opt-out first
        # -------------------------------------------------------------
        if self._matches_any(msg_clean, self.HOSTILE_PATTERNS):
            return {
                "action": "end",
                "message": f"Understood. We have stopped outreach for {merchant_name}. Thank you."
            }

        # -------------------------------------------------------------
        # PASS 2 FIX: Stage 2 - Check Explicit Intent BEFORE Auto-reply
        # e.g., "Thank you for contacting me directly... let's proceed"
        # contains "let's proceed", must NEVER be misclassified as canned auto-reply!
        # -------------------------------------------------------------
        if self._matches_any(msg_clean, self.INTENT_PATTERNS):
            return {
                "action": "send",
                "message": f"Great! Your promotion is now active on magicpin. We will monitor performance and share live stats."
            }

        # -------------------------------------------------------------
        # Stage 3 - Check Auto-Reply / Canned Message & Repetition
        # -------------------------------------------------------------
        is_canned = self._matches_any(msg_clean, self.AUTO_REPLY_PATTERNS)

        # Count consecutive identical messages from merchant in history
        identical_count = 1
        for past_msg in reversed(history):
            if past_msg.get("role") in ["user", "merchant"]:
                if past_msg.get("text", "").strip().lower() == msg_clean.lower():
                    identical_count += 1
                else:
                    break

        if is_canned or identical_count >= 2:
            # Auto-reply hell avoidance: If identical or canned multiple times, wait or end
            if identical_count >= 3:
                return {
                    "action": "end",
                    "message": None
                }
            return {
                "action": "wait",
                "message": None
            }

        # -------------------------------------------------------------
        # Stage 4 - Off-Topic Curveball / General Inquiries
        # -------------------------------------------------------------
        if re.search(r"\b(commission|rate|fee|charges|percentage)\b", msg_clean.lower()):
            return {
                "action": "send",
                "message": f"Standard magicpin commission is 12% on settled orders with 0 setup fee. Would you like to proceed with the proposed campaign? Reply YES to activate."
            }
        elif re.search(r"\b(help|support|manager|human|agent)\b", msg_clean.lower()):
            return {
                "action": "send",
                "message": f"Your dedicated account manager is assigned to {merchant_name}. Reply YES to request an immediate callback."
            }
        else:
            return {
                "action": "send",
                "message": f"Got it! We are here to help grow {merchant_name}. To move forward with the suggested promotion, reply YES."
            }

reply_engine = ReplyEngine()
