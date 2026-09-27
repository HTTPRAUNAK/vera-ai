"""
Reviews and loyalty composers:
- review_negative
- review_positive
- loyalty_tier_upgrade
- new_dish_launch
- cashback_campaign
- voucher_drop
"""

def compose_review_negative(trigger: dict, merchant: dict, category: dict) -> str:
    name = merchant.get("name", "Partner")
    payload = trigger.get("payload", {})
    issue = payload.get("negative_theme", "delivery delay and packaging")
    review_count = payload.get("review_count", "3 recent reviews")
    recovery_deal = payload.get("recovery_deal", "₹100 apology voucher on next order")

    return (
        f"Hi {name}, {review_count} highlighted issues regarding {issue}. "
        f"Win back affected diners by sending a '{recovery_deal}' to protect your 4+ star rating. "
        f"Reply YES to dispatch service recovery vouchers."
    )

def compose_review_positive(trigger: dict, merchant: dict, category: dict) -> str:
    name = merchant.get("name", "Partner")
    payload = trigger.get("payload", {})
    milestone = payload.get("milestone", "500 five-star reviews")
    rating = payload.get("rating", "4.8")
    loyalty_reward = payload.get("reward", "Extra 10% magicpin coins for all reviewers")

    return (
        f"Congratulations {name}! You just crossed {milestone} with a stellar {rating} rating. "
        f"Celebrate this milestone by gifting '{loyalty_reward}' to thank your top repeat customers. "
        f"Reply YES to announce the celebration reward."
    )

def compose_loyalty_tier_upgrade(trigger: dict, merchant: dict, category: dict) -> str:
    name = merchant.get("name", "Partner")
    payload = trigger.get("payload", {})
    new_tier = payload.get("tier", "Platinum Partner")
    cashback_boost = payload.get("cashback_boost", "15% magicPay cashback")

    return (
        f"Hi {name}, your consistent order volume has upgraded your outlet to {new_tier}! "
        f"This unlocks {cashback_boost} co-funded by magicpin to supercharge footfall. "
        f"Reply YES to enable your Platinum tier boost."
    )

def compose_new_dish_launch(trigger: dict, merchant: dict, category: dict) -> str:
    name = merchant.get("name", "Partner")
    payload = trigger.get("payload", {})
    dish_name = payload.get("dish_name", "Truffle Butter Paneer")
    intro_price = payload.get("introductory_price", "₹279")

    return (
        f"Hi {name}, introducing your new '{dish_name}'? "
        f"Give it instant traction by offering an introductory price of {intro_price} to your first 50 tasters. "
        f"Reply YES to promote your new dish launch."
    )

def compose_cashback_campaign(trigger: dict, merchant: dict, category: dict) -> str:
    name = merchant.get("name", "Partner")
    payload = trigger.get("payload", {})
    cashback_rate = payload.get("cashback_rate", "20% cashback")
    min_spend = payload.get("min_spend", "₹500")

    return (
        f"Hi {name}, merchants running magicPay cashback see a 32% increase in repeat visits. "
        f"Launch a '{cashback_rate} on orders above {min_spend}' weekend campaign to drive direct settlement. "
        f"Reply YES to activate the cashback campaign."
    )

def compose_voucher_drop(trigger: dict, merchant: dict, category: dict) -> str:
    name = merchant.get("name", "Partner")
    payload = trigger.get("payload", {})
    voucher_count = payload.get("voucher_count", "50 exclusive vouchers")
    voucher_value = payload.get("voucher_value", "₹150 off on orders above ₹400")

    return (
        f"Hi {name}, drive quick volume with a limited flash drop of {voucher_count} offering '{voucher_value}'. "
        f"These flash drops typically sell out within 3 hours. "
        f"Reply YES to release the flash vouchers."
    )
