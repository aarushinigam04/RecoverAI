def evaluate_policy(payment, diagnosis):
    """
    RecoverAI V2 Policy and Safety Engine.

    Decision flow:
        AI Diagnosis
            ↓
        Hard Safety Gates
            ↓
        Systemic Failure Handling
            ↓
        High-Value Gate
            ↓
        Diagnostic Confidence Gate
            ↓
        Recovery Probability Gate
            ↓
        Action Validation
            ↓
        Final Decision

    V2 CHANGE:
    Recovery probability now directly influences whether an
    automatically retryable action is approved.

    Safety rules always override the AI recommendation.

    Evaluation methodology is NOT changed by this file.
    """

    # =========================================================
    # EXTRACT DIAGNOSIS
    # =========================================================

    diagnosis_info = diagnosis.get("diagnosis", {})
    recovery = diagnosis.get("recovery", {})

    category = diagnosis_info.get(
        "category",
        "Unknown"
    )

    confidence = diagnosis_info.get(
        "confidence",
        0
    )

    action = recovery.get(
        "recommended_action",
        "require_human_review"
    )

    success_probability = recovery.get(
        "success_probability",
        0
    )

    amount = payment.amount or 0

    risk_flags = list(
        diagnosis.get("risk_flags", [])
    )

    def add_risk_flag(flag):
        if flag not in risk_flags:
            risk_flags.append(flag)

    # =========================================================
    # GATE 1 — HARD SAFETY RESTRICTIONS
    # =========================================================
    #
    # These ALWAYS override diagnosis and probability.
    #
    # Fraud
    # Customer opted out
    # Payment already captured
    # Duplicate event
    # Retry limit exceeded
    # Account closed
    #
    # None may receive automatic recovery.
    # =========================================================

    restricted_categories = {
        "Fraud Detected",
        "Customer Opted Out",
        "Payment Already Captured",
        "Duplicate Event",
        "Retry Limit Exceeded",
        "Account Closed"
    }

    if category in restricted_categories:

        add_risk_flag(
            "restricted_recovery_action"
        )

        if category == "Fraud Detected":

            add_risk_flag(
                "fraud_detected"
            )

            reason = (
                "Potential fraud detected. Automatic "
                "payment recovery is blocked."
            )

        elif category == "Customer Opted Out":

            reason = (
                "Customer has opted out of payment recovery. "
                "Automatic recovery is blocked."
            )

        elif category == "Payment Already Captured":

            reason = (
                "Payment has already been captured. "
                "Retry is prohibited."
            )

        elif category == "Duplicate Event":

            reason = (
                "Duplicate payment event detected. "
                "Retry is prohibited."
            )

        elif category == "Account Closed":

            add_risk_flag(
                "account_closed"
            )

            reason = (
                "The associated account is closed. "
                "Automatic payment recovery is blocked."
            )

        else:

            reason = (
                "Payment has exceeded the permitted retry "
                "limit. Further automatic retry is prohibited."
            )

        return {
            "policy_decision": "BLOCKED",
            "approved_action": "do_not_retry",
            "reason": reason,
            "risk_flags": risk_flags
        }

    # =========================================================
    # GATE 2 — SYSTEMIC PAYMENT SERVICE FAILURE
    # =========================================================
    #
    # Payment API/service unavailable is treated as a
    # systemic outage rather than a normal transaction failure.
    #
    # Probability does NOT override this safety path.
    # =========================================================

    if category == "Payment Service Unavailable":

        add_risk_flag(
            "systemic_payment_service_failure"
        )

        add_risk_flag(
            "circuit_breaker_backoff"
        )

        return {
            "policy_decision": "APPROVED",
            "approved_action": "retry_payment",
            "reason": (
                "Payment service is temporarily unavailable. "
                "Recovery is approved as a delayed retry with "
                "backoff to avoid repeated requests during a "
                "possible systemic outage."
            ),
            "risk_flags": risk_flags
        }

    # =========================================================
    # GATE 3 — HIGH-VALUE PAYMENT
    # =========================================================
    #
    # Amount is authoritative.
    #
    # >= ₹50,000 → human review.
    #
    # This overrides probability and AI recommendation.
    # =========================================================

    if amount >= 50000:

        add_risk_flag(
            "high_value_payment"
        )

        add_risk_flag(
            "human_approval_required"
        )

        return {
            "policy_decision": "NEEDS_HUMAN",
            "approved_action": "require_human_review",
            "reason": (
                "High-value payment requires human review "
                "before recovery can proceed."
            ),
            "risk_flags": risk_flags
        }

    # =========================================================
    # GATE 4 — DIAGNOSTIC CONFIDENCE
    # =========================================================
    #
    # Existing frozen threshold:
    #
    # confidence < 0.60 → human review
    #
    # This threshold is not changed by V2.
    # =========================================================

    if confidence < 0.60:

        add_risk_flag(
            "low_diagnostic_confidence"
        )

        return {
            "policy_decision": "NEEDS_HUMAN",
            "approved_action": "require_human_review",
            "reason": (
                "Diagnostic confidence is below the minimum "
                "threshold for automatic recovery."
            ),
            "risk_flags": risk_flags
        }

    # =========================================================
    # GATE 5 — ACTION VALIDATION
    # =========================================================

    supported_actions = {
        "retry_payment",
        "retry_after_funds_added",
        "ask_customer_to_update_payment_method",
        "ask_customer_to_contact_bank",
        "do_not_retry",
        "require_human_review"
    }

    if action not in supported_actions:

        add_risk_flag(
            "unsupported_recovery_action"
        )

        return {
            "policy_decision": "NEEDS_HUMAN",
            "approved_action": "require_human_review",
            "reason": (
                "The AI recommended an unsupported recovery "
                "action. Human review is required."
            ),
            "risk_flags": risk_flags
        }

    # =========================================================
    # GATE 6 — NON-AUTOMATIC ACTIONS
    # =========================================================
    #
    # These actions do not represent an automatic retry.
    #
    # They should not be incorrectly blocked merely because
    # their probability is below the automatic retry threshold.
    # =========================================================

    non_automatic_actions = {
        "ask_customer_to_update_payment_method",
        "ask_customer_to_contact_bank",
        "require_human_review",
        "do_not_retry"
    }

    if action in non_automatic_actions:

        if action == "require_human_review":

            add_risk_flag(
                "human_approval_required"
            )

            return {
                "policy_decision": "NEEDS_HUMAN",
                "approved_action": "require_human_review",
                "reason": (
                    "The recovery recommendation requires "
                    "human review."
                ),
                "risk_flags": risk_flags
            }

        if action == "do_not_retry":

            return {
                "policy_decision": "BLOCKED",
                "approved_action": "do_not_retry",
                "reason": (
                    "The recommended recovery action is to "
                    "avoid retrying this payment."
                ),
                "risk_flags": risk_flags
            }

        return {
            "policy_decision": "APPROVED",
            "approved_action": action,
            "reason": (
                "The recommended recovery action requires "
                "customer interaction rather than an automatic "
                "payment retry."
            ),
            "risk_flags": risk_flags
        }

    # =========================================================
    # GATE 7 — RECOVERY PROBABILITY
    # =========================================================
    #
    # This is the V2 decision-making improvement.
    #
    # < 0.40
    #     → BLOCKED
    #
    # 0.40–0.59
    #     → NEEDS_HUMAN
    #
    # >= 0.60
    #     → automatic recovery eligible
    #
    # Therefore predicted recovery probability has real
    # decision-making consequences.
    # =========================================================

    if success_probability < 0.40:

        add_risk_flag(
            "low_recovery_probability"
        )

        return {
            "policy_decision": "BLOCKED",
            "approved_action": "do_not_retry",
            "reason": (
                "Predicted recovery probability is below "
                "the minimum threshold for automatic recovery."
            ),
            "risk_flags": risk_flags
        }

    if success_probability < 0.60:

        add_risk_flag(
            "moderate_recovery_probability"
        )

        add_risk_flag(
            "human_approval_required"
        )

        return {
            "policy_decision": "NEEDS_HUMAN",
            "approved_action": "require_human_review",
            "reason": (
                "Predicted recovery probability is moderate. "
                "Human review is required before automatic "
                "recovery."
            ),
            "risk_flags": risk_flags
        }

    # =========================================================
    # FINAL AUTOMATIC APPROVAL
    # =========================================================

    return {
        "policy_decision": "APPROVED",
        "approved_action": action,
        "reason": (
            "Recovery recommendation satisfies all safety "
            "policies, has sufficient diagnostic confidence, "
            "and has sufficient predicted recovery probability "
            "for automatic recovery."
        ),
        "risk_flags": risk_flags
    }