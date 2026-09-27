"""
Customer facing composers:
- customer_recall
- appointment_reminder
Hinglish and English aware.
"""

def compose_customer_recall(trigger: dict, merchant: dict, customer: dict) -> str:
    cust_name = customer.get("name", "Valued Customer")
    merchant_name = merchant.get("name", "our outlet")
    fav_item = customer.get("favorite_item") or (merchant.get("offers", {}).get("signature_items") or ["Signature Special"])[0]
    days_since = customer.get("days_since_last_visit", "30 days")
    lang = customer.get("language", "english").lower()
    voucher = customer.get("offer", "₹100 off on your next bill")

    if "hinglish" in lang or "hi" in lang:
        return (
            f"Namaste {cust_name}! {days_since} ho gaye aapko {merchant_name} par dekhe hue. "
            f"Aapka favorite '{fav_item}' aapka intezar kar raha hai. Use karein '{voucher}'. "
            f"Reply KAREIN to claim your offer."
        )
    else:
        return (
            f"Hi {cust_name}, it has been {days_since} since your last visit to {merchant_name}. "
            f"Your favorite '{fav_item}' is waiting for you with '{voucher}'. "
            f"Reply YES to claim your exclusive voucher."
        )

def compose_appointment_reminder(trigger: dict, merchant: dict, customer: dict) -> str:
    cust_name = customer.get("name", "Customer")
    merchant_name = merchant.get("name", "our salon")
    service = customer.get("service", "Hair Spa & Styling")
    app_time = customer.get("appointment_time", "tomorrow at 4:00 PM")
    lang = customer.get("language", "english").lower()

    if "hinglish" in lang or "hi" in lang:
        return (
            f"Namaste {cust_name}! {merchant_name} par aapka '{service}' appointment {app_time} ke liye scheduled hai. "
            f"Reply HAAN to confirm your booking."
        )
    else:
        return (
            f"Hi {cust_name}, reminder for your '{service}' appointment at {merchant_name} on {app_time}. "
            f"Reply YES to confirm your booking."
        )
