# vera-bot — magicpin AI Challenge

An autonomous, deterministic WhatsApp merchant-assistant bot engineered to outperform magicpin's Vera assistant by proactively engaging merchants across 25 dynamic context triggers while eliminating intent-handoff failures and auto-reply pollution.

---

## 📋 Table of Contents
1. [Challenge Overview](#challenge-overview)
2. [Architecture & 4 Context Layers](#architecture--4-context-layers)
3. [5-Endpoint HTTP Contract](#5-endpoint-http-contract)
4. [25 Seed Trigger Composers](#25-seed-trigger-composers)
5. [Reply State Machine & 4 Replay Scenarios](#reply-state-machine--4-replay-scenarios)
6. [5-Dimension Judging Rubric & Anti-Patterns](#5-dimension-judging-rubric--anti-patterns)
7. [Judge Simulator (`judge_simulator.py`)](#judge-simulator)
8. [Interactive Web Dashboard](#interactive-web-dashboard)
9. [The Testing & Debugging Journey](#the-testing--debugging-journey)
10. [Local Setup & Testing](#local-setup--testing)
11. [Cloud Deployment (Render)](#cloud-deployment-render)

---

## Challenge Overview

The **magicpin AI Challenge** required building a WhatsApp merchant-assistant bot that beats magicpin's own assistant, **Vera**, at proactively engaging merchants. Rather than just measuring text generation, the challenge specified an exact architecture and rigorous grading criteria:
- **4 Context Layers** feeding every message.
- **Fixed 5-Endpoint HTTP Contract** with idempotency and version-conflict handling.
- **5-Dimension LLM Judging Rubric** (scored 0–10) penalizing explicit anti-patterns (generic offers, multiple CTAs, buried CTAs, hallucinated data, ignoring language preference, re-introducing yourself).
- **Named Failure Modes of Vera** to visibly avoid: auto-reply pollution, intent-handoff failure, generic discount copy, and low engagement frequency.
- **100% Deterministic Engine at Runtime**: Zero runtime LLM dependencies ensure grading never depends on third-party API availability, rate limits, or network latency.

---

## Architecture & 4 Context Layers

Every message composed by `vera-bot` integrates information from four distinct context layers:

```
┌────────────────────────────────────────────────────────┐
│                      Context Layers                    │
├────────────────────────────────────────────────────────┤
│ 1. Category  : Tone, domain vocabulary, allowed offers │
│ 2. Merchant  : Identity, signature items, metrics      │
│ 3. Trigger   : Event prompting outreach (IPL, dips...) │
│ 4. Customer  : Identity, visits, Hinglish preference   │
└─────────────────────────────────────────┬──────────────┘
                                          │
                                          ▼
                         ┌─────────────────────────────────┐
                         │   Deterministic Composer Table  │
                         │      (25 Dedicated Engines)     │
                         └────────────────┬────────────────┘
                                          │
                                          ▼
                         ┌─────────────────────────────────┐
                         │ Specific WhatsApp Outreach Copy │
                         │   (Single Prominent Action CTA) │
                         └─────────────────────────────────┘
```

1. **Category**: Tone, vocabulary, and permissible promotions tailored to business type (e.g. F&B, Salon, Retail).
2. **Merchant**: Identity, performance metrics, signature dishes/catalog, owner name, and recent review themes.
3. **Trigger**: Specific trigger event and metadata (e.g. order dip percentage, distance to competitor, IPL match start time, days to subscription expiry).
4. **Customer** *(optional / customer-facing)*: Name, favorite items, days since last visit, and language preference (English vs. Hinglish).

---

## 5-Endpoint HTTP Contract

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/v1/healthz` | Health check endpoint returning `{"status": "ok"}` |
| `GET` | `/v1/metadata` | Bot metadata, team identity, supported trigger kinds, rubric alignment |
| `POST` | `/v1/context` | Idempotent, versioned context pushes. Rejects stale versions (`< current`) or conflicting payloads (`== current` with different hash) with `HTTP 409 Conflict` |
| `POST` | `/v1/tick` | Proactive outreach dispatcher; accepts trigger payloads and outputs proactive send actions |
| `POST` | `/v1/reply` | Inbound WhatsApp reply state machine; returns `action` (`send` / `wait` / `end`) + response copy |

---

## 25 Seed Trigger Composers

`vera-bot` implements dedicated composers for all 25 seed triggers across five categories, ensuring zero generic filler:

### 1. Performance (4 Triggers)
- `performance_dip`: Spotlight signature items with promo pricing to quickly recover weekly volume dips.
- `table_booking_dip`: Counter empty table reservations during specific shifts with high-value perks.
- `high_cart_abandonment`: Deliver targeted cart recovery deals to convert pending checkouts.
- `organic_traffic_spike`: Capitalize on surging profile views by turning browsers into buyers via BOGO deals.

### 2. Market Events (7 Triggers)
- `competitor_opening`: Defend local turf against new rivals within radius using high-margin hero item specials.
- `competitor_promo`: Counter aggressive competitor discounts with premium combos instead of destructive price wars.
- `nearby_event`: Target college fest / conference footfalls with grab-and-go meal boxes.
- `festival_upcoming`: Context-aware festival catalog (handles 4-day rush vs. 180-day advance catering differently).
- `ipl_match`: Timed promotions activating match-day snacking combos during high-order innings.
- `payday_weekend`: Feature luxury tasting menus and premium buffets to capture surging spend.
- `rainy_day`: Trigger comfort food delivery pushes (hot chai, pakoras, soups) during neighborhood rains.

### 3. Operational & Inventory (6 Triggers)
- `inventory_expiry`: Flash clearance discounts liquidating expiring perishables to stop dead-stock loss.
- `batch_recall`: High-priority quarantine alerts referencing supplier, product, and batch numbers.
- `subscription_renewal`: Correctly distinguishes upcoming renewals from expired memberships (no "renews in 0 days").
- `happy_hour`: Activates afternoon footfall boosters during slow weekday hours.
- `weekend_rush`: Kitchen prep expediter combos designed for high-throughput weekend volume.
- `seasonal_menu_switch`: Seasonal menu launches (e.g. summer mocktails, winter sizzlers).

### 4. Reviews & Loyalty (6 Triggers)
- `review_negative`: Targeted apology vouchers addressing specific customer complaint themes.
- `review_positive`: Milestone celebration perks honoring 500+ or 1,000+ five-star reviews.
- `loyalty_tier_upgrade`: Crown Platinum unlock announcing co-funded magicPay cashback.
- `new_dish_launch`: Introductory trial pricing for the first 50 tasters of a newly launched dish.
- `cashback_campaign`: MagicPay cashback drives directly boosting weekend order repeat rates.
- `voucher_drop`: High-urgency flash voucher drops (e.g. 50 or 75 limited vouchers).

### 5. Customer Facing (2 Triggers)
- `customer_recall`: Hinglish-aware re-engagement referencing customer's favorite dish and days absent.
- `appointment_reminder`: Hinglish-aware reminder for scheduled salon or dining bookings.

---

## Reply State Machine & 4 Replay Scenarios

The reply engine uses an **adversarially ordered state machine** designed to prevent Vera's worst failure modes:

```
Inbound Merchant Message
         │
         ▼
[1. Hostile / Opt-out?] ──────────► Action: END (Polite closure)
         │ No
         ▼
[2. Intent Confirmation?] ────────► Action: SEND (Activate campaign immediately)
         │ No
         ▼
[3. Canned Auto-Reply / Loop?] ───► Action: WAIT / END (Prevent auto-reply pollution)
         │ No
         ▼
[4. Off-Topic / General Curveball] ► Action: SEND (12% commission, manager callback, etc.)
```

### The 4 Replay Scenarios
1. **Auto-Reply Hell**: Four identical canned replies in a row (e.g. *"Thank you for contacting us. We will get back to you shortly"*). The bot detects the loop and returns `action: wait` (and `action: end` on repeated loops) with `message: null`, refusing to pollute turns.
2. **Intent Transition**: Merchant replies *"Thank you for contacting me directly... let's proceed"*. Because Intent is checked **before** Auto-Reply, the bot immediately activates the campaign (`action: send`) without re-qualifying the merchant.
3. **Hostile / Opt-Out**: Merchant replies *"Please stop messaging me and remove my number"*. The bot immediately terminates outreach (`action: end`) with polite confirmation.
4. **Off-Topic Curveball**: Merchant asks *"What is your commission rate?"*. Bot answers with exact numbers (12% standard commission, ₹0 setup fee) and redirects with a single CTA.

---

## 5-Dimension Judging Rubric & Anti-Patterns

Messages are scored on a **0–10 scale** across five dimensions:
1. **Specificity**: Presence of currency (`₹`), percentages, exact distances, dates, and dish names.
2. **Category Fit**: Vocabulary matched to F&B, Salon, or Retail domain.
3. **Merchant Fit**: Explicitly incorporates merchant name and catalog signature items.
4. **Trigger Relevance**: Directly tied to the triggering context without filler.
5. **Engagement Compulsion**: Exactly one prominent, actionable CTA at the end of the message.

### Anti-Patterns Checked & Eliminated
- ❌ Re-introducing bot identity (*"Hi I am Vera"*)
- ❌ Multiple conflicting CTAs
- ❌ Buried CTAs (placing action instructions in the middle of copy)
- ❌ Generic filler copy (*"Get flat 50% discount on everything"*)
- ❌ Hallucinated data or impossible phrasing (*"renews in 0 days"*)
- ❌ Ignoring language preferences (failing to send Hinglish when requested)

---

## Judge Simulator (`judge_simulator.py`)

A built-in self-checking test tool that evaluates messages against the complete 5-dimension rubric:

```bash
# Evaluate all 25 seed triggers
python judge_simulator.py --all

# Evaluate a specific trigger kind
python judge_simulator.py performance_dip
```

Average score achieved across all 25 triggers: **8.66 / 10.0** with **0 Anti-Patterns flagged**.

---

## Interactive Web Dashboard

When the server runs, visiting `GET /` or `GET /dashboard` opens an interactive dashboard providing:
- **Contract & Metadata Inspector**
- **Context Layer & 409 Conflict Sandbox**
- **25 Proactive Trigger Dispatcher** with live preview and rubric scorecards
- **Interactive WhatsApp Phone Simulator** with 1-click execution of all 4 Replay Scenarios

---

## The Testing & Debugging Journey

As documented in the challenge brief, key real-world challenges were overcome during development:

1. **Sandbox Network Limits & Quotas**: Cloud sandboxes blocked external LLM APIs; free-tier keys suffered from rate limits (HTTP 429) and silent 5/10 fallbacks. The solution was engineering a 100% deterministic, zero-latency composer and an offline rubric evaluator.
2. **Windows Socket Permissions Conflict**: Flask's Werkzeug development server failed on Windows with socket access errors (*"An attempt was made to access a socket in a way forbidden by its access permissions"*). The solution was transitioning to `waitress`, a pure-Python WSGI server (`serve_waitress.py`), which also resolved dynamic `$PORT` handling.
3. **GitHub Push Protection & Leaked Secret Purge**: An earlier commit contained an API key in the test scripts. The git history was squashed into a clean commit, removing all sensitive secrets.
4. **Edge Cases Caught in Adversarial Passes**:
   - `subscription_renewal`: Fixed 0 days remaining from outputting "renews in 0 days" to cleanly detecting expired state.
   - `festival_upcoming`: Distant festivals (e.g. Diwali in 180 days) switch from "just 180 days away" to advance booking and early-bird catering.
   - `reply_engine`: Reordered intent detection before auto-reply to eliminate intent-handoff failures.

---

## Local Setup & Testing

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Automated Test Suite
```bash
pytest test_bot.py -v
```
*(Runs 14 automated unit tests covering all endpoints, 25 triggers, 4 replay scenarios, 409 conflict, and judge rubric simulator).*

### 3. Start the Server (Waitress WSGI)
```bash
python serve_waitress.py
```
Server starts on `http://127.0.0.1:5000`.

### 4. Run Live Verification
```bash
python test_live.py http://127.0.0.1:5000
```

---

## Cloud Deployment (Render)

The project includes `render.yaml` and `Procfile` configured for Render Web Service deployment:

- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn -w 2 -b 0.0.0.0:$PORT bot:app`
- **Environment**: Python 3.11+
- **Auto-detected PORT**: `bot.py` and `serve_waitress.py` bind `0.0.0.0:$PORT` in cloud environments and fallback to `127.0.0.1:5000` locally.
