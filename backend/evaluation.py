from backend.database import SessionLocal
from backend import models
from backend.context_builder import build_payment_context
from backend.ai_agent import diagnose_payment
from backend.policy_engine import evaluate_policy


# ============================================================
# FROZEN ACTION-SPECIFIC GROUND-TRUTH OUTCOME MODEL
# ============================================================
#
# These probabilities are fixed BEFORE evaluation.
# They must NOT be changed after seeing evaluation results.
#
# The probabilities represent the expected outcome of a
# PARTICULAR recovery action for a PARTICULAR failure category.
#
# ------------------------------------------------------------
# Failure Category              Retry   Payment Link   Stop
# ------------------------------------------------------------
# Insufficient Funds              10%        65%          0%
# Card Expired                    10%        65%          0%
# Bank Timeout                    80%        40%          0%
# Gateway/API Timeout             80%        40%          0%
# Network Error                   80%        40%          0%
# Fraud Suspected                  0%         0%          0%
# Customer Opted Out               0%         0%          0%
#
#
# HIGH-VALUE PAYMENTS
# ------------------------------------------------------------
# High-value payments ALWAYS require human review.
#
# Human Review is NOT assigned an automated recovery
# probability.
#
# Human-review cases:
#   - remain in the common evaluation denominator
#   - are NOT counted as automated recovery successes
#   - are reported separately
#
#
# RECOVERAI POLICY VIOLATIONS
# ------------------------------------------------------------
# RecoverAI must never automatically retry or use a payment
# link for:
#
#   - High-value payments
#   - Fraud
#   - Customer opted out
#
# Such events are counted as:
#
#   recoverai_policy_violations
#
# Expected value for a correctly functioning system:
#
#   0
#
#
# NAIVE BASELINE
# ------------------------------------------------------------
# The baseline intentionally performs:
#
#   retry_payment
#
# for EVERY eligible payment.
#
# Therefore retrying:
#
#   - fraud
#   - customer opted out
#   - high-value payments
#
# is expected baseline behavior, NOT a RecoverAI bug.
#
# These events are counted separately as:
#
#   baseline_unsafe_actions
#
#
# ORACLE
# ------------------------------------------------------------
# Oracle chooses the highest-probability VALID action while
# respecting the same safety constraints.
#
# Fraud              -> Stop
# Customer opted out -> Stop
# High-value          -> Human Review
#
# Oracle is therefore a safety-constrained upper bound.
#
#
# DENOMINATOR
# ------------------------------------------------------------
# The same held-out failed-payment population is used for:
#
#   RecoverAI
#   Naive Baseline
#   Oracle
#
# Human-review cases remain in the denominator.
#
#
# IMPORTANT
# ------------------------------------------------------------
# The AI diagnosis success_probability is NEVER used as
# evaluation ground truth.
#
# The frozen table above is the independent outcome model.
# ============================================================


FROZEN_OUTCOME_MODEL = {

    "insufficient funds": {
        "retry_payment": 0.10,
        "payment_link": 0.65,
        "stop": 0.00
    },

    "card expired": {
        "retry_payment": 0.10,
        "payment_link": 0.65,
        "stop": 0.00
    },

    "bank timeout": {
        "retry_payment": 0.80,
        "payment_link": 0.40,
        "stop": 0.00
    },

    "gateway timeout": {
        "retry_payment": 0.80,
        "payment_link": 0.40,
        "stop": 0.00
    },

    "payment api unavailable": {
        "retry_payment": 0.80,
        "payment_link": 0.40,
        "stop": 0.00
    },

    "network timeout": {
        "retry_payment": 0.80,
        "payment_link": 0.40,
        "stop": 0.00
    },

    "network connectivity issue": {
        "retry_payment": 0.80,
        "payment_link": 0.40,
        "stop": 0.00
    },

    "fraud detected": {
        "retry_payment": 0.00,
        "payment_link": 0.00,
        "stop": 0.00
    },

    "customer opted out": {
        "retry_payment": 0.00,
        "payment_link": 0.00,
        "stop": 0.00
    }
}


# Categories that must never receive an automatic recovery action.

FRAUD_CATEGORIES = {
    "fraud detected",
    "fraud suspected"
}

OPT_OUT_CATEGORIES = {
    "customer opted out"
}


# ------------------------------------------------------------
# Helper: normalize failure reason
# ------------------------------------------------------------

def normalize_reason(reason):
    if not reason:
        return ""

    return reason.strip().lower()


# ------------------------------------------------------------
# Helper: classify failure category
# ------------------------------------------------------------

def get_category(reason):

    reason = normalize_reason(reason)

    if reason in FROZEN_OUTCOME_MODEL:
        return reason

    # Timeout-related categories
    if "bank timeout" in reason:
        return "bank timeout"

    if "gateway timeout" in reason:
        return "gateway timeout"

    if "payment api unavailable" in reason:
        return "payment api unavailable"

    if "network timeout" in reason:
        return "network timeout"

    if "network connectivity" in reason:
        return "network connectivity issue"

    # Insufficient funds
    if "insufficient funds" in reason:
        return "insufficient funds"

    # Expired card
    if "card expired" in reason:
        return "card expired"

    # Fraud
    if "fraud" in reason:
        return "fraud detected"

    # Opted out
    if "opted out" in reason:
        return "customer opted out"

    return None


# ------------------------------------------------------------
# Helper: high-value detection
# ------------------------------------------------------------

def is_high_value(payment):

    return payment.amount >= 50000


# ------------------------------------------------------------
# Helper: get RecoverAI action
# ------------------------------------------------------------

def get_recoverai_action(policy):

    decision = policy.get("policy_decision")

    action = policy.get("approved_action")

    if decision == "NEEDS_HUMAN":
        return "human_review"

    if decision == "BLOCKED":
        return "stop"

    if decision == "APPROVED":

        if action == "retry_payment":
            return "retry_payment"

        if action == "ask_customer_to_update_payment_method":
            return "payment_link"

        if action == "do_not_retry":
            return "stop"

        if action == "require_human_review":
            return "human_review"

    return "unknown"


# ------------------------------------------------------------
# Helper: probability for an action
# ------------------------------------------------------------

def get_action_probability(category, action):

    if action == "human_review":
        return None

    if action == "stop":
        return 0.0

    if category not in FROZEN_OUTCOME_MODEL:
        return 0.0

    return FROZEN_OUTCOME_MODEL[category].get(
        action,
        0.0
    )


# ------------------------------------------------------------
# Oracle action
# ------------------------------------------------------------

def get_oracle_action(payment, category):

    # High-value always requires human review.

    if is_high_value(payment):
        return "human_review"

    # Fraud must stop.

    if category in FRAUD_CATEGORIES:
        return "stop"

    # Opted-out customers must stop.

    if category in OPT_OUT_CATEGORIES:
        return "stop"

    # Unknown categories are conservatively stopped.

    if category not in FROZEN_OUTCOME_MODEL:
        return "stop"

    probabilities = FROZEN_OUTCOME_MODEL[category]

    retry_probability = probabilities["retry_payment"]
    payment_link_probability = probabilities["payment_link"]

    if payment_link_probability > retry_probability:
        return "payment_link"

    if retry_probability > payment_link_probability:
        return "retry_payment"

    return "stop"


# ============================================================
# MAIN EVALUATION
# ============================================================

def run_recoverai_evaluation(
    db,
    held_out_size=200
):

    # --------------------------------------------------------
    # Select failed payments
    # --------------------------------------------------------

    payments = (
        db.query(models.Payment)
        .filter(models.Payment.status == "failed")
        .order_by(models.Payment.id)
        .limit(held_out_size)
        .all()
    )

    total = len(payments)

    if total == 0:

        return {
            "evaluation_population": {
                "eligible_payments": 0
            },
            "recoverai": {},
            "baseline": {},
            "oracle": {},
            "comparison": {},
            "safety": {}
        }

    # --------------------------------------------------------
    # RecoverAI counters
    # --------------------------------------------------------

    recoverai_estimated_recovered = 0.0
    recoverai_human_review = 0
    recoverai_blocked = 0

    recoverai_policy_violations = 0

    recoverai_action_correct = 0

    diagnosis_correct = 0

    # --------------------------------------------------------
    # Baseline counters
    # --------------------------------------------------------

    baseline_estimated_recovered = 0.0

    baseline_unsafe_actions = 0

    # --------------------------------------------------------
    # Oracle
    # --------------------------------------------------------

    oracle_estimated_recovered = 0.0
    oracle_human_review = 0

    # --------------------------------------------------------
    # Category statistics
    # --------------------------------------------------------

    category_counts = {}

    # ========================================================
    # Evaluate every held-out payment
    # ========================================================

    for payment in payments:

        reason = normalize_reason(
            payment.failure_reason
        )

        category = get_category(reason)

        if category is None:
            category = "unknown"

        category_counts[category] = (
            category_counts.get(category, 0) + 1
        )

        # ----------------------------------------------------
        # Build context
        # ----------------------------------------------------

        context = build_payment_context(
            payment.id,
            db
        )

        if not context:
            continue

        # ----------------------------------------------------
        # AI diagnosis
        # ----------------------------------------------------

        diagnosis = diagnose_payment(context)

        # ----------------------------------------------------
        # Policy decision
        # ----------------------------------------------------

        policy = evaluate_policy(
            payment=payment,
            diagnosis=diagnosis
        )

        recoverai_action = get_recoverai_action(
            policy
        )

        # ====================================================
        # DIAGNOSIS ACCURACY
        # ====================================================

        diagnosed_category = normalize_reason(
            diagnosis
            .get("diagnosis", {})
            .get("category", "")
        )

        expected_category = category

        diagnosis_category_map = {

            "insufficient funds":
                "insufficient funds",

            "card expired":
                "card expired",

            "bank timeout":
                "bank timeout",

            "gateway timeout":
                "gateway timeout",

            "payment api unavailable":
                "payment api unavailable",

            "network timeout":
                "network timeout",

            "network connectivity issue":
                "network connectivity issue",

            "fraud detected":
                "fraud detected",

            "customer opted out":
                "customer opted out"
        }

        normalized_diagnosed_category = (
            diagnosis_category_map.get(
                diagnosed_category,
                diagnosed_category
            )
        )

        if normalized_diagnosed_category == expected_category:
            diagnosis_correct += 1

        # ====================================================
        # RECOVERAI SAFETY CHECK
        # ====================================================

        violation = False

        # High-value must be human review.

        if is_high_value(payment):

            if recoverai_action != "human_review":
                violation = True

        # Fraud must stop.

        if category in FRAUD_CATEGORIES:

            if recoverai_action not in {
                "stop",
                "human_review"
            }:
                violation = True

        # Opt-out must stop.

        if category in OPT_OUT_CATEGORIES:

            if recoverai_action not in {
                "stop",
                "human_review"
            }:
                violation = True

        if violation:

            recoverai_policy_violations += 1

        # ====================================================
        # RECOVERAI RESULT
        # ====================================================

        if recoverai_action == "human_review":

            recoverai_human_review += 1

        elif recoverai_action == "stop":

            recoverai_blocked += 1

        elif recoverai_action in {
            "retry_payment",
            "payment_link"
        }:

            probability = get_action_probability(
                category,
                recoverai_action
            )

            recoverai_estimated_recovered += (
                probability
            )

        # ====================================================
        # ACTION-SELECTION ACCURACY
        # ====================================================

        oracle_action = get_oracle_action(
            payment,
            category
        )

        if recoverai_action == oracle_action:
            recoverai_action_correct += 1

        # ====================================================
        # ORACLE OUTCOME
        # ====================================================

        if oracle_action == "human_review":

            oracle_human_review += 1

        else:

            oracle_probability = get_action_probability(
                category,
                oracle_action
            )

            oracle_estimated_recovered += (
                oracle_probability or 0.0
            )

        # ====================================================
        # NAIVE BASELINE
        # ====================================================

        baseline_action = "retry_payment"

        # Baseline safety violations are intentional.

        if (
            is_high_value(payment)
            or category in FRAUD_CATEGORIES
            or category in OPT_OUT_CATEGORIES
        ):

            baseline_unsafe_actions += 1

        baseline_probability = get_action_probability(
            category,
            baseline_action
        )

        baseline_estimated_recovered += (
            baseline_probability
        )

    # ========================================================
    # RATES
    # ========================================================

    recoverai_rate = (
        recoverai_estimated_recovered / total
    ) * 100

    baseline_rate = (
        baseline_estimated_recovered / total
    ) * 100

    oracle_rate = (
        oracle_estimated_recovered / total
    ) * 100

    uplift = (
        recoverai_rate - baseline_rate
    )

    oracle_gap = (
        oracle_rate - recoverai_rate
    )

    # ========================================================
    # ACCURACY
    # ========================================================

    diagnosis_accuracy = (
        diagnosis_correct / total
    ) * 100

    action_selection_accuracy = (
        recoverai_action_correct / total
    ) * 100

    # ========================================================
    # SAFETY RATES
    # ========================================================

    recoverai_policy_violation_rate = (
        recoverai_policy_violations / total
    ) * 100

    baseline_unsafe_action_rate = (
        baseline_unsafe_actions / total
    ) * 100

    human_review_rate = (
        recoverai_human_review / total
    ) * 100

    blocked_rate = (
        recoverai_blocked / total
    ) * 100

    # ========================================================
    # RETURN RESULTS
    # ========================================================

    return {

        "evaluation_population": {

            "eligible_payments": total,

            "category_distribution": category_counts
        },

        "recoverai": {

            "estimated_recovered": round(
                recoverai_estimated_recovered,
                2
            ),

            "automated_recovery_rate_percent": round(
                recoverai_rate,
                2
            ),

            "blocked": recoverai_blocked,

            "human_review": recoverai_human_review,

            "human_review_rate_percent": round(
                human_review_rate,
                2
            ),

            "diagnosis_accuracy_percent": round(
                diagnosis_accuracy,
                2
            ),

            "action_selection_accuracy_percent": round(
                action_selection_accuracy,
                2
            )
        },

        "baseline": {

            "strategy": "retry_everything",

            "estimated_recovered": round(
                baseline_estimated_recovered,
                2
            ),

            "recovery_rate_percent": round(
                baseline_rate,
                2
            )
        },

        "oracle": {

            "type": "safety_constrained_oracle",

            "estimated_recovered": round(
                oracle_estimated_recovered,
                2
            ),

            "recovery_rate_percent": round(
                oracle_rate,
                2
            ),

            "human_review": oracle_human_review
        },

        "comparison": {

            "recoverai_uplift_percentage_points": round(
                uplift,
                2
            ),

            "oracle_gap_percentage_points": round(
                oracle_gap,
                2
            )
        },

        "safety": {

            "recoverai_policy_violations":
                recoverai_policy_violations,

            "recoverai_policy_violation_rate_percent":
                round(
                    recoverai_policy_violation_rate,
                    2
                ),

            "baseline_unsafe_actions":
                baseline_unsafe_actions,

            "baseline_unsafe_action_rate_percent":
                round(
                    baseline_unsafe_action_rate,
                    2
                ),

            "recoverai_blocked_actions":
                recoverai_blocked,

            "recoverai_human_review_cases":
                recoverai_human_review
        }
    }


# ============================================================
# COMMAND-LINE EXECUTION
# ============================================================

if __name__ == "__main__":

    db = SessionLocal()

    try:

        print("=" * 70)
        print("RecoverAI Frozen Evaluation")
        print("=" * 70)

        print()
        print(
            "Outcome model: FROZEN ACTION-SPECIFIC TABLE"
        )

        print(
            "Held-out population: 200 failed payments"
        )

        print(
            "Ground truth: independent action-specific outcome model"
        )

        print()

        results = run_recoverai_evaluation(
            db,
            held_out_size=200
        )

        print("=" * 70)
        print("EVALUATION POPULATION")
        print("=" * 70)

        print(
            "Eligible payments:",
            results["evaluation_population"]
            ["eligible_payments"]
        )

        print()

        print("=" * 70)
        print("RECOVERAI")
        print("=" * 70)

        print(
            "Estimated recovered:",
            results["recoverai"]
            ["estimated_recovered"]
        )

        print(
            "Automated recovery rate:",
            results["recoverai"]
            ["automated_recovery_rate_percent"],
            "%"
        )

        print(
            "Diagnosis accuracy:",
            results["recoverai"]
            ["diagnosis_accuracy_percent"],
            "%"
        )

        print(
            "Action-selection accuracy:",
            results["recoverai"]
            ["action_selection_accuracy_percent"],
            "%"
        )

        print(
            "Blocked:",
            results["recoverai"]
            ["blocked"]
        )

        print(
            "Human review:",
            results["recoverai"]
            ["human_review"]
        )

        print()

        print("=" * 70)
        print("NAIVE BASELINE")
        print("=" * 70)

        print(
            "Strategy:",
            results["baseline"]["strategy"]
        )

        print(
            "Estimated recovered:",
            results["baseline"]
            ["estimated_recovered"]
        )

        print(
            "Recovery rate:",
            results["baseline"]
            ["recovery_rate_percent"],
            "%"
        )

        print()

        print("=" * 70)
        print("SAFETY-CONSTRAINED ORACLE")
        print("=" * 70)

        print(
            "Estimated recovered:",
            results["oracle"]
            ["estimated_recovered"]
        )

        print(
            "Recovery rate:",
            results["oracle"]
            ["recovery_rate_percent"],
            "%"
        )

        print(
            "Human review:",
            results["oracle"]
            ["human_review"]
        )

        print()

        print("=" * 70)
        print("COMPARISON")
        print("=" * 70)

        print(
            "RecoverAI uplift:",
            results["comparison"]
            ["recoverai_uplift_percentage_points"],
            "percentage points"
        )

        print(
            "Oracle gap:",
            results["comparison"]
            ["oracle_gap_percentage_points"],
            "percentage points"
        )

        print()

        print("=" * 70)
        print("SAFETY METRICS")
        print("=" * 70)

        print(
            "RecoverAI policy violations:",
            results["safety"]
            ["recoverai_policy_violations"]
        )

        print(
            "RecoverAI policy violation rate:",
            results["safety"]
            ["recoverai_policy_violation_rate_percent"],
            "%"
        )

        print(
            "Baseline unsafe actions:",
            results["safety"]
            ["baseline_unsafe_actions"]
        )

        print(
            "Baseline unsafe action rate:",
            results["safety"]
            ["baseline_unsafe_action_rate_percent"],
            "%"
        )

        print()

        print("=" * 70)
        print("Frozen evaluation completed.")
        print("=" * 70)

    finally:

        db.close()