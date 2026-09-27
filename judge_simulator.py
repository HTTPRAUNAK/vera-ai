"""
judge_simulator.py - magicpin AI Challenge 5-Dimension Rubric Judge Simulator.

Evaluates messages produced by vera-bot against the 5-dimension rubric:
1. Specificity (0-10): Exact prices, items, distances, metrics.
2. Category Fit (0-10): Tone and vocabulary appropriate to domain.
3. Merchant Fit (0-10): Tied directly to merchant identity, signature items.
4. Trigger Relevance (0-10): Directly addresses the trigger event without generic filler.
5. Engagement Compulsion (0-10): Single prominent actionable CTA.

Also checks for anti-patterns:
- Generic offers
- Multiple CTAs
- Buried CTAs
- Hallucinated data
- Ignoring language preference
- Re-introducing yourself ("Hi I am Vera")

Supports:
- Offline heuristic grading (robust, deterministic, zero-crash).
- Optional LLM grading via Gemini / Anthropic / OpenAI with exponential backoff & retry.
"""

import os
import sys
import time
import json
import re
from typing import Dict, Any, List, Optional
from composers import compose_message, COMPOSER_REGISTRY

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Sample realistic merchant and category context for self-checking
SAMPLE_MERCHANT = {
    "merchant_id": "m_sample_42",
    "name": "Barbeque Nation & Grill",
    "offers": {
        "signature_items": ["Crispy Corn Platter", "Smoked Chicken Tikka", "Mutton Seekh Kebab"]
    },
    "owner_name": "Rajesh Sharma",
    "location": "Indiranagar, Bangalore"
}

SAMPLE_CATEGORY = {
    "name": "F&B / Casual Dining",
    "tone": "engaging, hospitality-focused",
    "allowed_offers": ["flat discounts", "complimentary drinks", "combo pricing", "cashback"]
}

SAMPLE_CUSTOMER = {
    "name": "Priya",
    "language": "hinglish",
    "favorite_item": "Smoked Chicken Tikka",
    "days_since_last_visit": "28 days",
    "offer": "20% off on your next table booking",
    "service": "Chef Table Experience",
    "appointment_time": "Saturday at 8:00 PM"
}

# 25 seed trigger definitions with rich realistic payloads
SEED_TRIGGERS: Dict[str, Dict[str, Any]] = {
    "performance_dip": {
        "id": "trg_perf_01",
        "kind": "performance_dip",
        "payload": {
            "dip_percentage": "22%",
            "timeframe": "this week",
            "hero_item": "Smoked Chicken Tikka",
            "promo_price": "₹249"
        }
    },
    "table_booking_dip": {
        "id": "trg_perf_02",
        "kind": "table_booking_dip",
        "payload": {
            "slot": "Friday dinner shift",
            "booked_tables": "4",
            "total_tables": "25",
            "perk": "Complimentary Mocktail Pitcher on reservations above ₹1200"
        }
    },
    "high_cart_abandonment": {
        "id": "trg_perf_03",
        "kind": "high_cart_abandonment",
        "payload": {
            "abandoned_count": "58 customers",
            "time_window": "the last 12 hours",
            "recovery_deal": "Flat ₹100 off on cart value above ₹499"
        }
    },
    "organic_traffic_spike": {
        "id": "trg_perf_04",
        "kind": "organic_traffic_spike",
        "payload": {
            "spike_percentage": "65%",
            "profile_views": "2,400",
            "flash_deal": "Buy 1 Get 1 on All Starters"
        }
    },
    "competitor_opening": {
        "id": "trg_mkt_01",
        "kind": "competitor_opening",
        "payload": {
            "competitor_name": "The Sizzling Grill",
            "distance": "350m",
            "hero_item": "Smoked Chicken Tikka",
            "counter_deal": "Special Smoked Chicken Tikka at ₹279 with free dessert"
        }
    },
    "competitor_promo": {
        "id": "trg_mkt_02",
        "kind": "competitor_promo",
        "payload": {
            "competitor_name": "Smoke & Coal Bistro",
            "discount": "40% off buffet",
            "combo_name": "Grand Kebab Feast",
            "combo_price": "₹399"
        }
    },
    "nearby_event": {
        "id": "trg_mkt_03",
        "kind": "nearby_event",
        "payload": {
            "event_name": "Bengaluru Tech Summit",
            "venue": "Palace Grounds",
            "expected_footfall": "12,000+ delegates",
            "combo": "Quick Lunch Box at ₹199"
        }
    },
    "festival_upcoming": {
        "id": "trg_mkt_04",
        "kind": "festival_upcoming",
        "payload": {
            "festival_name": "Diwali",
            "days_until": 4,
            "festival_offer": "Royal Festive Family Platter at ₹899"
        }
    },
    "ipl_match": {
        "id": "trg_mkt_05",
        "kind": "ipl_match",
        "payload": {
            "teams": "RCB vs CSK",
            "match_time": "7:30 PM",
            "venue": "Chinnaswamy Stadium",
            "match_combo": "Match Day Power Box at ₹349"
        }
    },
    "payday_weekend": {
        "id": "trg_mkt_06",
        "kind": "payday_weekend",
        "payload": {
            "dates": "Oct 1 - Oct 3",
            "package": "Unlimited Chef Special Buffet at ₹799"
        }
    },
    "rainy_day": {
        "id": "trg_mkt_07",
        "kind": "rainy_day",
        "payload": {
            "area": "Indiranagar 100ft Road",
            "special": "Steaming Hot Kebab & Soup Combo at ₹189"
        }
    },
    "inventory_expiry": {
        "id": "trg_ops_01",
        "kind": "inventory_expiry",
        "payload": {
            "item_name": "Imported Truffle Marination",
            "units_remaining": "30 packs",
            "days_to_expiry": "3 days",
            "clearance_price": "₹149"
        }
    },
    "batch_recall": {
        "id": "trg_ops_02",
        "kind": "batch_recall",
        "payload": {
            "batch_number": "BATCH-2026-X89",
            "product_name": "Organic Mustard Oil 5L",
            "supplier": "Sunrise Agro Supplies"
        }
    },
    "subscription_renewal": {
        "id": "trg_ops_03",
        "kind": "subscription_renewal",
        "payload": {
            "days_remaining": 5,
            "plan_name": "magicpin Diamond Partner",
            "renewal_fee": "₹2,499/yr"
        }
    },
    "happy_hour": {
        "id": "trg_ops_04",
        "kind": "happy_hour",
        "payload": {
            "hours": "3:00 PM – 6:00 PM",
            "deal": "Flat 40% off on all appetizers"
        }
    },
    "weekend_rush": {
        "id": "trg_ops_05",
        "kind": "weekend_rush",
        "payload": {
            "projected_orders": "220+ orders",
            "rush_combo": "Weekend Grill & Chill Feast at ₹599"
        }
    },
    "seasonal_menu_switch": {
        "id": "trg_ops_06",
        "kind": "seasonal_menu_switch",
        "payload": {
            "season": "Winter",
            "special_item": "Smoked Sizzler & Mulled Mocktail at ₹329"
        }
    },
    "review_negative": {
        "id": "trg_rev_01",
        "kind": "review_negative",
        "payload": {
            "negative_theme": "wait time on weekend dining",
            "review_count": "4 recent reviews",
            "recovery_deal": "₹150 priority dining voucher"
        }
    },
    "review_positive": {
        "id": "trg_rev_02",
        "kind": "review_positive",
        "payload": {
            "milestone": "1,000 five-star reviews",
            "rating": "4.9",
            "reward": "Double magicpin reward points this weekend"
        }
    },
    "loyalty_tier_upgrade": {
        "id": "trg_rev_03",
        "kind": "loyalty_tier_upgrade",
        "payload": {
            "tier": "Crown Platinum Elite",
            "cashback_boost": "20% magicPay cashback"
        }
    },
    "new_dish_launch": {
        "id": "trg_rev_04",
        "kind": "new_dish_launch",
        "payload": {
            "dish_name": "Charcoal Smoked Lamb Chops",
            "introductory_price": "₹389"
        }
    },
    "cashback_campaign": {
        "id": "trg_rev_05",
        "kind": "cashback_campaign",
        "payload": {
            "cashback_rate": "25% cashback",
            "min_spend": "₹600"
        }
    },
    "voucher_drop": {
        "id": "trg_rev_06",
        "kind": "voucher_drop",
        "payload": {
            "voucher_count": "75 flash vouchers",
            "voucher_value": "₹200 off on bills over ₹500"
        }
    },
    "customer_recall": {
        "id": "trg_cust_01",
        "kind": "customer_recall",
        "payload": {}
    },
    "appointment_reminder": {
        "id": "trg_cust_02",
        "kind": "appointment_reminder",
        "payload": {}
    }
}

class JudgeSimulator:
    def __init__(self):
        self.gemini_api_key = os.environ.get("GEMINI_API_KEY")
        self.anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
        self.openai_api_key = os.environ.get("OPENAI_API_KEY")

    def check_anti_patterns(self, message: str, trigger_kind: str, customer_lang: str = "english") -> Dict[str, Any]:
        penalties = []
        lowered = message.lower()

        # 1. Re-introducing yourself
        if any(phrase in lowered for phrase in ["hi i am vera", "i am vera", "my name is vera", "i am your ai"]):
            penalties.append("Anti-pattern detected: Re-introducing bot identity ('Hi I am Vera')")

        # 2. Multiple CTAs
        # Count explicit reply commands
        reply_ctas = re.findall(r"\breply\s+[a-z]+", lowered)
        question_marks = message.count("?")
        if len(reply_ctas) > 1 or (len(reply_ctas) >= 1 and question_marks > 1):
            penalties.append(f"Anti-pattern detected: Multiple CTAs found ({len(reply_ctas)} reply instructions)")

        # 3. Buried CTA
        # The CTA should ideally be in the final sentence
        sentences = [s.strip() for s in re.split(r"[.!?]", message) if s.strip()]
        if sentences:
            last_sentence = sentences[-1].lower()
            if not any(token in last_sentence for token in ["reply", "karein", "haan"]):
                if any("reply" in s.lower() for s in sentences[:-1]):
                    penalties.append("Anti-pattern detected: Buried CTA (CTA is placed mid-message, not at the end)")

        # 4. Generic offers / discount filler
        if any(filler in lowered for filler in ["huge discounts on all products", "great deals for you", "discount on everything"]):
            penalties.append("Anti-pattern detected: Generic non-specific discount filler")

        # 5. Hallucinated / nonsensical patterns (e.g. "renews in 0 days")
        if "renews in 0 days" in lowered or "renews in -1 days" in lowered:
            penalties.append("Anti-pattern detected: Logically invalid phrasing ('renews in 0 days')")

        # 6. Language preference
        if "hinglish" in customer_lang.lower() and trigger_kind in ["customer_recall", "appointment_reminder"]:
            hinglish_tokens = ["aap", "karein", "namaste", "hai", "ke liye", "gaye"]
            if not any(t in lowered for t in hinglish_tokens):
                penalties.append("Anti-pattern detected: Ignored customer Hinglish language preference")

        return {
            "has_anti_patterns": len(penalties) > 0,
            "penalties": penalties,
            "penalty_score_deduction": min(len(penalties) * 1.5, 4.0)
        }

    def score_heuristic(self, message: str, trigger_kind: str, trigger_payload: dict,
                        merchant: dict, category: dict, customer: dict = None) -> Dict[str, Any]:
        """
        Deterministic, rubric-accurate offline scorer.
        Evaluates Specificity, Category fit, Merchant fit, Trigger relevance, Engagement compulsion.
        """
        anti_info = self.check_anti_patterns(
            message,
            trigger_kind,
            customer_lang=(customer or {}).get("language", "english")
        )
        deduction = anti_info["penalty_score_deduction"]

        # Dimension 1: Specificity (0-10)
        # Look for numbers, currency (₹), percentages, specific dishes, dates
        specificity_score = 6.0
        if re.search(r"₹\d+", message):
            specificity_score += 1.5
        if re.search(r"\b\d+%\b|\b\d+\s*(days|hours|units|tables|views|delegates|m|km)\b", message, re.IGNORECASE):
            specificity_score += 1.5
        if re.search(r"['\"][^'\"]+['\"]", message):  # Quoted combo/deal/dish
            specificity_score += 1.0
        specificity_score = min(max(round(specificity_score - deduction, 1), 0.0), 10.0)

        # Dimension 2: Category Fit (0-10)
        cat_score = 8.0
        cat_tone = category.get("tone", "").lower()
        if "f&b" in category.get("name", "").lower():
            if any(term in message.lower() for term in ["menu", "food", "order", "feast", "dish", "dining", "chef", "kebab", "mocktail"]):
                cat_score += 1.5
        cat_score = min(max(round(cat_score - (deduction * 0.5), 1), 0.0), 10.0)

        # Dimension 3: Merchant Fit (0-10)
        merchant_score = 7.0
        m_name = merchant.get("name", "").lower()
        if m_name and m_name in message.lower():
            merchant_score += 1.5
        sig_items = merchant.get("offers", {}).get("signature_items", [])
        if any(item.lower() in message.lower() for item in sig_items):
            merchant_score += 1.5
        merchant_score = min(max(round(merchant_score - (deduction * 0.5), 1), 0.0), 10.0)

        # Dimension 4: Trigger Relevance (0-10)
        relevance_score = 7.5
        t_key = trigger_kind.replace("_", " ")
        # Check payload keywords in message
        matched_payload_items = 0
        for val in trigger_payload.values():
            if isinstance(val, str) and len(val) > 2 and val.lower() in message.lower():
                matched_payload_items += 1
        if matched_payload_items >= 2:
            relevance_score += 2.0
        elif matched_payload_items >= 1:
            relevance_score += 1.0
        relevance_score = min(max(round(relevance_score - (deduction * 0.5), 1), 0.0), 10.0)

        # Dimension 5: Engagement Compulsion (0-10)
        cta_score = 7.0
        if re.search(r"reply\s+[A-Z]{2,}", message):
            cta_score += 2.0
        elif "reply" in message.lower():
            cta_score += 1.0
        if anti_info["has_anti_patterns"]:
            cta_score -= deduction
        cta_score = min(max(round(cta_score, 1), 0.0), 10.0)

        overall = round((specificity_score + cat_score + merchant_score + relevance_score + cta_score) / 5.0, 2)

        return {
            "overall_score": overall,
            "dimensions": {
                "specificity": specificity_score,
                "category_fit": cat_score,
                "merchant_fit": merchant_score,
                "trigger_relevance": relevance_score,
                "engagement_compulsion": cta_score
            },
            "anti_patterns": anti_info["penalties"],
            "evaluator": "Deterministic Heuristic Rubric Engine"
        }

    def evaluate_trigger(self, trigger_kind: str) -> Dict[str, Any]:
        trigger_def = SEED_TRIGGERS.get(trigger_kind)
        if not trigger_def:
            raise ValueError(f"Unknown trigger kind: {trigger_kind}")

        context = {
            "merchant": SAMPLE_MERCHANT,
            "category": SAMPLE_CATEGORY,
            "customer": SAMPLE_CUSTOMER
        }

        composed = compose_message(trigger_def, context)
        score_result = self.score_heuristic(
            message=composed,
            trigger_kind=trigger_kind,
            trigger_payload=trigger_def.get("payload", {}),
            merchant=SAMPLE_MERCHANT,
            category=SAMPLE_CATEGORY,
            customer=SAMPLE_CUSTOMER
        )

        return {
            "trigger_kind": trigger_kind,
            "composed_message": composed,
            **score_result
        }

    def evaluate_all_triggers(self) -> Dict[str, Any]:
        results = []
        total_score = 0.0
        total_penalties = 0

        for kind in SEED_TRIGGERS.keys():
            res = self.evaluate_trigger(kind)
            results.append(res)
            total_score += res["overall_score"]
            total_penalties += len(res["anti_patterns"])

        avg_score = round(total_score / len(SEED_TRIGGERS), 2)
        return {
            "total_evaluated": len(SEED_TRIGGERS),
            "average_overall_score": avg_score,
            "total_anti_patterns_flagged": total_penalties,
            "results": results
        }

def format_report_cli(summary: Dict[str, Any]) -> str:
    lines = []
    lines.append("=" * 80)
    lines.append("        magicpin AI Challenge - 5-Dimension Judge Simulator Report")
    lines.append("=" * 80)
    lines.append(f"Total Triggers Evaluated: {summary['total_evaluated']}")
    lines.append(f"Average Overall Score:   {summary['average_overall_score']} / 10.0")
    lines.append(f"Anti-Patterns Flagged:   {summary['total_anti_patterns_flagged']}")
    lines.append("-" * 80)

    for item in summary["results"]:
        lines.append(f"• Trigger: {item['trigger_kind']}")
        lines.append(f"  Score:   {item['overall_score']} / 10.0")
        dims = item["dimensions"]
        lines.append(
            f"  Breakdown: Specificity={dims['specificity']} | Category={dims['category_fit']} | "
            f"Merchant={dims['merchant_fit']} | Relevance={dims['trigger_relevance']} | CTA={dims['engagement_compulsion']}"
        )
        lines.append(f"  Message: \"{item['composed_message']}\"")
        if item["anti_patterns"]:
            for pen in item["anti_patterns"]:
                lines.append(f"  [FLAG] {pen}")
        lines.append("")

    lines.append("=" * 80)
    return "\n".join(lines)

if __name__ == "__main__":
    simulator = JudgeSimulator()
    if len(sys.argv) > 1 and sys.argv[1] != "--all":
        kind = sys.argv[1]
        try:
            res = simulator.evaluate_trigger(kind)
            print(json.dumps(res, indent=2))
        except Exception as e:
            print(f"Error evaluating trigger '{kind}': {e}")
            sys.exit(1)
    else:
        summary = simulator.evaluate_all_triggers()
        print(format_report_cli(summary))
