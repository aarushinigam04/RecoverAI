<div align="center">

# 🔁 RecoverAI

### AI-Assisted Payment Revenue Recovery System

**Razorpay AI Buildathon · Track 03**

An agentic system that monitors failed payments, builds payment context, diagnoses the failure,
recommends **bounded** recovery actions, enforces policy & safety gates, executes approved actions in a
controlled **Test Mode / synthetic** environment, records every outcome, and measures recovery performance.

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00)](https://www.sqlalchemy.org/)
[![Razorpay](https://img.shields.io/badge/Razorpay-Test%20Mode-0C2451)](https://razorpay.com/)
[![Status](https://img.shields.io/badge/Status-Final%20Buildathon%20Prototype-blue)]()

> ### 🛡️ Architecture principle
> **AI recommends → Policy authorizes → Executor acts → Outcome is observed → Revenue is measured.**

</div>

---

## Table of Contents

1. [Overview](#overview)
2. [The Problem](#the-problem)
3. [Features](#features)
4. [How It Works — Pipeline Flow](#how-it-works--pipeline-flow)
5. [System Architecture](#system-architecture)
6. [Agent Reasoning Model](#agent-reasoning-model)
7. [AI Diagnosis Engine](#ai-diagnosis-engine)
8. [Policy & Safety Engine](#policy--safety-engine)
9. [Recovery Execution](#recovery-execution)
10. [Recovery Case Lifecycle](#recovery-case-lifecycle)
11. [Data & Persistence](#data--persistence)
12. [API Endpoints](#api-endpoints)
13. [RecoverAI Command Center (Dashboard)](#recoverai-command-center-dashboard)
14. [Evaluation & Validated Benchmark](#evaluation--validated-benchmark)
15. [Failure Testing](#failure-testing)
16. [Technology Stack](#technology-stack)
17. [Project Structure](#project-structure)
18. [Running Locally](#running-locally)
19. [Demo Flows](#demo-flows)
20. [Design Principles](#design-principles)
21. [Roadmap — Future Extensions](#roadmap--future-extensions)
22. [Project Status](#project-status)

---

## Overview

**RecoverAI** turns *failed payments* — which are revenue at risk — into a **structured, safe recovery
workflow**. Instead of blindly retrying every failure, the system:

1. **Observes** each failed payment and builds a rich context (payment, customer, history, limits).
2. **Diagnoses** *why* the payment failed and estimates the probability of successful recovery.
3. **Recommends** a bounded, policy-aware recovery action.
4. **Gates** every recommendation through an independent policy & safety engine.
5. **Executes** only approved actions in a controlled **Test Mode / synthetic** environment.
6. **Records** every attempt and outcome, then **measures** recovered revenue and recovery rate.

The heart of the design is a strict **separation of duties**: the AI layer *never directly executes a
financial action* — a deterministic policy layer decides what is **approved**, **blocked**, or sent to
**human review**.

---

## The Problem

> Failed payments represent revenue at risk — but **not every failed payment should simply be retried.**

Different failures demand different responses:

| Failure | Right response |
|---|---|
| 💸 Insufficient funds | Customer action (add funds) |
| 📅 Expired card | Customer updates payment method |
| 🌐 Temporary bank / gateway / network / service failure | Safe to **retry** |
| 🚫 Fraud, duplicate events, opt-outs, already-captured payments | **Do not** auto-retry |
| 🧑‍⚖️ High-value or uncertain cases | **Human review** |

RecoverAI distinguishes between these cases and routes each one through an appropriate,
policy-controlled workflow — instead of applying the same action to every failure.

---

## Features

- ✅ **End-to-end recovery pipeline** — from failed payment event to measured revenue recovery
- ✅ **Context builder** — assembles payment, customer, history & policy context
- ✅ **AI-assisted diagnosis** — deterministic & auditable failure classification (safe-by-design)
- ✅ **Recovery probability & expected value estimation**
- ✅ **Independent Policy & Safety Engine** — `APPROVED` / `BLOCKED` / `NEEDS_HUMAN`
- ✅ **Bounded recovery actions** — retry, notify customer, contact-bank workflow, human review, stop
- ✅ **Controlled Test Mode execution** — Razorpay Test Mode + synthetic outcome model
- ✅ **Full outcome persistence** — payment attempts & recovery cases
- ✅ **Command Center dashboard** — live monitoring & decision interface
- ✅ **AI Decision Center** — *read-only* preview of diagnosis & policy decisions (no execution)
- ✅ **Reproducible evaluation** — frozen 500-payment benchmark, baseline uplift, safety checks
- ✅ **Failure-mode testing** — duplicates, timeouts, opt-outs, fraud, high-value approvals & more

---

## How It Works — Pipeline Flow

```text
Payment / Synthetic Event
        │
        ▼
Payment Record
        │
        ▼
Context Builder
        │
        ▼
AI Diagnosis
        │
        ▼
Policy & Safety Engine
        │
        ▼
Recovery Executor
        │
        ▼
Controlled Test / Synthetic Execution
        │
        ▼
Payment Attempt / Outcome
        │
        ▼
Metrics + Evaluation
        │
        ▼
RecoverAI Command Center
```

The dashboard also exposes a **read-only AI Decision Center** that previews a diagnosis and its policy
decision *without executing any recovery action* — a safe way to inspect what the system *would* do.

---

## System Architecture

```text
Payment / Synthetic Data
        │
        ▼
FastAPI Backend
        │
        ▼
Context Builder
        │
        ▼
AI Diagnosis
        │
        ▼
Policy / Safety Gate
        │
   ┌─────┼─────────┐
   ▼     ▼         ▼
APPROVED BLOCKED   NEEDS_HUMAN
   │     (stopped)  (escalated)
   ▼
Recovery Executor
   │
   ▼
Outcome / Attempts
   │
   ├──────────────┐
   ▼              ▼
Metrics          Dashboard
```

### 🛡️ Architectural safety boundary

RecoverAI enforces a strict separation between **AI recommendation**, **policy authorization**, and
**action execution**:

- The **AI diagnosis layer** never directly executes financial actions.
- The **policy engine** independently decides whether a recommendation is *allowed*, *blocked*, or
  requires human review.
- **Only an approved decision** ever reaches the recovery executor.

### Core pipeline responsibilities

| Component | Responsibility |
|---|---|
| **Event / Payment intake** | A failed payment (webhook or synthetic) becomes a payment record |
| **Context Builder** | Collects payment details, failure reason, customer, history, attempts & limits |
| **AI Diagnosis** | Classifies the failure, explains it, estimates recovery probability |
| **Policy & Safety Engine** | Applies limits, risk rules, consent & retry controls → approve / block / escalate |
| **Recovery Executor** | Runs only the approved action (retry, notify, escalate…) in controlled mode |
| **Outcome Monitor** | Persists the attempt result & recovery outcome |
| **Metrics & Evaluation** | Computes recovery, execution, safety & evaluation metrics |
| **Command Center** | Presents cases, decisions, audit trails and revenue impact |

---

## Agent Reasoning Model

RecoverAI behaves like a **bounded autonomous agent**:

```text
  OBSERVE
     │
     ▼
   REASON
     │
     ▼
   DECIDE
     │
     ▼
    ACT
     │
     ▼
OBSERVE OUTCOME
     │
     ▼
  MEASURE
```

> The loop is **bounded**: after measuring an outcome, the agent may *reassess* with a fresh decision —
> but only up to the configured retry limit, after which the case is stopped.

| Step | What happens |
|---|---|
| **Observe** | Collect payment details, failure reason, history, attempts & recovery context |
| **Reason** | Classify the failure and estimate recovery likelihood |
| **Decide** | Select one *bounded* action based on confidence, amount, risk flags, retry limits & restrictions |
| **Act** | Execute **only** the action permitted by policy |
| **Observe Outcome** | Record the resulting attempt & outcome |
| **Measure** | Calculate recovery, execution, safety & evaluation metrics |

---

## AI Diagnosis Engine

The current implementation uses a **deterministic, auditable diagnosis engine** rather than an
unrestricted production LLM. This keeps every decision explainable and testable.

### Failure categories handled

| Group | Categories |
|---|---|
| 🔁 **Retry-eligible (temporary)** | Bank Timeout · Gateway Timeout · Network Timeout / Connectivity · Payment API Unavailable · LLM Timeout |
| 💳 **Needs customer action** | Insufficient Funds · Card Expired · Invalid Payment Details · Bank Declined |
| 🚫 **Do-not-retry** | Fraud Detected · Duplicate Event · Payment Already Captured · Retry Limit Exceeded · Customer Opted Out |
| 🧑‍⚖️ **Escalate / review** | High-Value Payment · Invalid Payment ID · Other Failure |

> The policy engine decides the *final* outcome for any category; the grouping above shows the typical
> first response each failure receives.

### Structured diagnosis output

Every diagnosis produces structured, machine-readable fields:

- **Failure category** & human-readable **explanation**
- **Confidence** in the diagnosis
- **Recommended action**
- **Success probability** & **expected recovery** (₹)
- **Delay** before the action
- **Risk flags**
- **Human-review requirement**

---

## Policy & Safety Engine

The policy layer is **fully independent** of the diagnosis layer — a recommendation never bypasses it.

```text
     AI Diagnosis / Agent
  (recommendation + confidence)
              │
              ▼
       Policy Engine
    (limits • risk • consent)
              │
   ┌──────────┼───────────┐
   ▼          ▼           ▼
Allowed    Blocked     Needs Human
(execute) (stopped /   Review
           recorded)   (human decides:
                        approve / adjust /
                        escalate / reject)
   │
   ▼
Executor
(approved action)
   │
   ▼
Outcome / Attempts
   │
   ▼
Audit Log + Metrics
(AI + policy + action)
```

> Only an **Allowed** decision (or a **human-approved** one from review) reaches the **Executor**.
> Everything — AI recommendation, policy verdict and executed action — is written to the **Audit Log**.

### Current safety behavior

- 🚫 **Restricted categories** can be blocked outright
- 💰 **High-value payments** can require human review
- ⚠️ **Low-confidence recommendations** can require human review
- 🔒 **Unsupported actions** are never auto-executed
- 📉 **Low-probability recovery actions** can be blocked or escalated
- 👤 **Customer-directed actions** (e.g. "ask customer to add funds") can be approved *without* treating
  them as unrestricted automatic retries
- 🔌 **Payment-service availability failures** can follow an approved retry path

---

## Recovery Execution

### Supported recovery actions

| Action | Purpose |
|---|---|
| 🔁 **Payment retry** | Retry a temporary failure |
| ✉️ **Ask customer to update payment method** | Expired / invalid card |
| ⏳ **Retry after customer update** | Payment method / funds updated |
| 🏦 **Contact-bank workflow** | Bank-side issues |
| 🧑‍⚖️ **Human review** | High-value / uncertain cases |
| ⏹️ **Stop / block** | Fraud, opt-outs, exhausted retries |

Execution results are persisted as **payment attempts** and **recovery outcomes**.

The current implementation uses a **deterministic test / synthetic outcome model** for repeatable,
evaluation-friendly results.

> ### ⚠️ Razorpay integration is used in **Test Mode only**.

---

## Recovery Case Lifecycle

Every failure becomes a **recovery case** that travels a controlled state machine:

```text
FAILED ──▶ ANALYZING ──▶ DECISION_READY ──▶ ACTION_EXECUTED ──▶ RECOVERED
```

**State transitions**

| From | Event | To |
|---|---|---|
| `FAILED` | Payment failure observed | `ANALYZING` |
| `ANALYZING` | Context built + diagnosis ready | `DECISION_READY` |
| `DECISION_READY` | Blocked / retries exhausted | `STOPPED` |
| `DECISION_READY` | Approval required (high-value / uncertain) | `HUMAN_REVIEW` |
| `HUMAN_REVIEW` | Approve / adjust recommendation | `DECISION_READY` (re-gated) |
| `DECISION_READY` | Approved action dispatched | `ACTION_EXECUTED` |
| `ACTION_EXECUTED` | Payment captured | `RECOVERED` |
| `ACTION_EXECUTED` | Provider / API failure | `ACTION_FAILED` |
| `ACTION_FAILED` | Choose next bounded step | `REASSESS` |
| `REASSESS` | Bounded retries remain | `DECISION_READY` (loop) |
| `REASSESS` | Retry limit reached | `STOPPED` |
| `RECOVERED` | Keep monitoring for anomalies | `REASSESS` |

The recovery loop is always **bounded** — a case cannot retry forever.

---

## Data & Persistence

**RecoverAI** uses **SQLAlchemy** with a relational database.

### Core entities

| Entity | Purpose |
|---|---|
| **Customers** | Customer context behind the payment |
| **Payments** | Current payment state & failure information |
| **Payment Attempts** | Recovery / retry history |
| **Recovery Cases** | Agent decision state per failed payment |
| **Recovery Actions** | Executed action records |

**Payment records** carry: `payment_id`, customer, amount, currency, status, `order_id`, failure reason,
and creation timestamp.

### Data flow (design target)

```text
webhook → payment_events → payments → recovery_case → agent_decision → recovery_action
       → payment_attempt → outcome → audit_log
```

The future data model also includes immutable event stores (`payment_events`), AI-audit stores
(`agent_decisions`), and end-to-end `audit_logs` for full traceability.

---

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/payments/failed` | List failed payments |
| `GET` | `/recovery/{payment_id}` | Recovery case for a payment |
| `GET` | `/ai-diagnosis/{payment_id}` | Diagnosis preview (read-only) |
| `GET` | `/policy/{payment_id}` | Policy decision preview (read-only) |
| `POST` | `/execute-recovery/{payment_id}` | Execute an approved recovery action |
| `GET` | `/dashboard` | Dashboard data |
| `GET` | `/metrics` | Recovery metrics |
| `POST` | `/razorpay/test-order` | Create a Razorpay Test Mode order |

> Interactive **Swagger** documentation is auto-generated by FastAPI at `/docs`.

---

## RecoverAI Command Center (Dashboard)

The dashboard is designed as a **monitoring and decision interface** — not a live-streaming event
console.

- 💹 **Revenue Recovery Overview**
- 📋 **Current database recovery metrics**
- ✅ **Validated benchmark results**
- 🔍 **Failure Analysis**
- 🥧 **Recovery Funnel**
- 🧠 **AI Decision Center** *(read-only preview)*
- 🛡️ **Policy & Safety Center**
- 🕘 **Recent Payments**
- 💰 Revenue at risk · Recovered revenue · Recovery rate · Execution success rate

---

## Evaluation & Validated Benchmark

RecoverAI ships **reproducible evaluation and validation scripts** covering:

- Recovery rate
- Execution success rate
- Diagnosis accuracy
- Action-selection accuracy
- Policy violations
- Blocked cases
- Human-review cases
- Baseline comparison & **recovery uplift**

### ✅ Validated 500-payment benchmark

| Metric | Result |
|---|---|
| Payments selected | 500 |
| Actions executed | 404 |
| Confirmed recoveries | 201 |
| Failed executions | 41 |
| Blocked by policy | 89 |
| Human review required | 7 |
| Unknown decisions | 0 |
| **Recovered amount** | **₹10,29,704.46** |
| Observed recovery rate | **40.20%** |
| Execution success rate | **49.75%** |

> These figures are the **validated 500-payment benchmark** and must not be confused with the current
> database state.

### 📌 Evaluation note

Frozen evaluator recovery figures are **probability-based expected values** — they are *not* equivalent
to actual rupee-weighted recovered revenue.

### Current Database vs Benchmark

RecoverAI deliberately distinguishes two metric sets:

| View | What it shows |
|---|---|
| **Current Database Metrics** | The *changing* state of the local project database |
| **Validated Benchmark Metrics** | The *preserved* results of the controlled 500-payment evaluation |

This prevents a changing database state from ever being presented as the official benchmark.

---

## Failure Testing

Important tested edge cases include:

- 🔁 Duplicate webhook
- ⏱️ LLM timeout
- 🔌 Payment API unavailable
- 💳 Payment already captured
- 🔢 Retry limit exceeded
- 🚫 Customer opted out
- 💰 High-value payment requiring approval
- 🆔 Invalid payment ID

---

## Technology Stack

| Layer | Technology |
|---|---|
| Backend | Python |
| API | FastAPI |
| ORM | SQLAlchemy |
| Database | Relational — SQLite or PostgreSQL configuration |
| Payment integration | **Razorpay Test Mode** |
| Dashboard | HTML · CSS · JavaScript |
| Evaluation | Pandas · NumPy |
| Test data | Synthetic |
| API server | Uvicorn |
| Configuration | python-dotenv |

---

## Project Structure

```text
RecoverAi/
├── backend/
│   ├── main.py                # FastAPI app & routes
│   ├── models.py              # SQLAlchemy models
│   ├── database.py            # DB session / engine
│   ├── context_builder.py     # Builds payment + history context
│   ├── ai_agent.py            # AI diagnosis agent
│   ├── policy_engine.py       # Independent policy & safety gate
│   ├── recovery.py            # Recovery case logic
│   ├── recovery_executor.py   # Executes approved actions
│   ├── action_executor.py     # Action primitives
│   ├── razorpay_client.py     # Razorpay Test Mode client
│   ├── metrics.py             # Recovery / execution metrics
│   ├── evaluation.py          # Reproducible evaluation
│   └── evaluation / experiment scripts
├── dashboard/
│   ├── index.html
│   ├── app.js
│   └── style.css
├── requirements.txt
├── README.md
├── .gitignore
└── .env                       # Local configuration (not committed)
```

---

## Running Locally

**1. Activate the virtual environment**

```powershell
.\.venv\Scripts\Activate.ps1
```

**2. Install dependencies**

```powershell
pip install -r requirements.txt
```

**3. Configure environment** — copy `.env.example` to `.env` and fill in Razorpay Test Mode keys (if used).

**4. Start the API**

```powershell
uvicorn backend.main:app --reload
```

**5. Open the apps**

| Resource | URL |
|---|---|
| Swagger docs | `http://127.0.0.1:8000/docs` |
| Dashboard | `http://127.0.0.1:8000/dashboard-ui/` |

> **Linux / macOS:** activate with `source .venv/bin/activate` — all other steps are identical.

---

## Demo Flows

### 🟢 Happy path — revenue recovered

```text
FAILED PAYMENT
     │
     ▼
AI DIAGNOSIS
     │
     ▼
RECOVERY PROBABILITY
     │
     ▼
POLICY CHECK
     │
     ▼
APPROVED ACTION
     │
     ▼
CONTROLLED EXECUTION
     │
     ▼
SUCCESS / FAILURE
     │
     ▼
₹ RECOVERED (on success)
```

### 🛑 Safety path — automatic action blocked

```text
HIGH-VALUE PAYMENT
     │
     ▼
AI RECOMMENDATION
     │
     ▼
POLICY CHECK
     │
     ▼
NEEDS HUMAN
     │
     ▼
AUTOMATIC ACTION BLOCKED
```

Together, these two flows demonstrate **both** revenue recovery **and** safe, bounded decision-making.

---

## Design Principles

1. 🤖 **AI assists** — it does not have unrestricted authority.
2. 🧱 **Policy is independent** from AI recommendation.
3. 🔐 **Only approved actions** can reach execution.
4. 🎯 **Recovery actions are bounded and controlled.**
5. ⚠️ **High-risk & uncertain cases can be escalated** to humans.
6. 📝 **Outcomes are recorded and measurable.**
7. 🧪 **Benchmark results stay separate** from changing database metrics.
8. 🧸 **Payment-provider integration remains in Test Mode.**
9. ♻️ **Evaluation is reproducible** — not optimized by repeatedly rerunning experiments.

---

## Roadmap — Future Extensions

> These are **future extensions** and are *not* claimed as current implemented features.

**Ingestion & reliability**

- Production-grade webhook ingestion with signature verification & idempotency persistence
- Async recovery workers + Redis-based queues / caching

**AI & intelligence**

- Production LLM integration with structured outputs
- Dedicated event & agent-decision storage
- More advanced recovery-prediction models
- More rigorous online experimentation

**Product & platform**

- React / Next.js dashboard architecture
- Expanded provider integrations
- Production authentication, observability & deployment

---

## Project Status

**RecoverAI — Final Buildathon Prototype** ✅

The current implementation includes:

- Payment failure data & **context building**
- **AI-assisted diagnosis** & recovery recommendation
- Independent **policy & safety gating**
- **Controlled recovery execution** (Razorpay Test Mode + synthetic outcomes)
- Outcome tracking & **recovery metrics**
- Frozen evaluation, failure testing & a **Command Center dashboard**
- Reproducible evaluation scripts

The project is ready for **final demonstration and submission review**.

---

## License

Developed as a **buildathon prototype** for the Razorpay AI Buildathon.
