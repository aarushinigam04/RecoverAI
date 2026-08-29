def evaluate_policy(payment, diagnosis):
    """
    Policy and Safety Engine for RecoverAI.

    Independently evaluates an AI-generated recovery recommendation
    and determines whether the recommendation is:
    - APPROVED
    - BLOCKED
    - NEEDS_HUMAN
    """

    # Get payment amount safely
    amount = payment.amount or 0

    # Extract AI diagnosis information
    category = diagnosis["diagnosis"]["category"]
    action = diagnosis["recovery"]["recommended_action"]
    confidence = diagnosis["diagnosis"]["confidence"]

    # Copy existing risk flags
    risk_flags = list(diagnosis.get("risk_flags", []))

    # Helper to avoid duplicate risk flags
    def add_risk_flag(flag):
        if flag not in risk_flags:
            risk_flags.append(flag)

    # ---------------------------------------------------------
    # POLICY 1: High-value payments
    # ---------------------------------------------------------
    if amount >= 2000:
        add_risk_flag("high_value_payment")

        return {
            "policy_decision": "NEEDS_HUMAN",
            "approved_action": "require_human_review",
            "reason": "High-value payment requires human review.",
            "risk_flags": risk_flags
        }

    # ---------------------------------------------------------
    # POLICY 2: Low-confidence diagnosis
    # ---------------------------------------------------------
    if confidence < 0.70:
        add_risk_flag("low_diagnostic_confidence")

        return {
            "policy_decision": "NEEDS_HUMAN",
            "approved_action": "require_human_review",
            "reason": "Diagnostic confidence is too low for automatic recovery.",
            "risk_flags": risk_flags
        }

    # ---------------------------------------------------------
    # POLICY 3: Payment already captured
    # ---------------------------------------------------------
    if category == "Payment Already Captured":
        add_risk_flag("restricted_recovery_action")

        return {
            "policy_decision": "BLOCKED",
            "approved_action": "do_not_retry",
            "reason": "Payment has already been captured. Retry is prohibited.",
            "risk_flags": risk_flags
        }

    # ---------------------------------------------------------
    # POLICY 4: Duplicate payment event
    # ---------------------------------------------------------
    if category == "Duplicate Event":
        add_risk_flag("restricted_recovery_action")

        return {
            "policy_decision": "BLOCKED",
            "approved_action": "do_not_retry",
            "reason": "Duplicate payment event detected. Retry is prohibited.",
            "risk_flags": risk_flags
        }

    # ---------------------------------------------------------
    # POLICY 5: Customer opted out
    # ---------------------------------------------------------
    if category == "Customer Opted Out":
        add_risk_flag("restricted_recovery_action")

        return {
            "policy_decision": "BLOCKED",
            "approved_action": "do_not_retry",
            "reason": "Customer has opted out of payment recovery.",
            "risk_flags": risk_flags
        }

    # ---------------------------------------------------------
    # POLICY 6: Retry limit exceeded
    # ---------------------------------------------------------
    if category == "Retry Limit Exceeded":
        add_risk_flag("restricted_recovery_action")

        return {
            "policy_decision": "NEEDS_HUMAN",
            "approved_action": "require_human_review",
            "reason": "Payment has exceeded the permitted retry limit.",
            "risk_flags": risk_flags
        }

    # ---------------------------------------------------------
    # POLICY 7: Approve normal recovery recommendations
    # ---------------------------------------------------------
    return {
        "policy_decision": "APPROVED",
        "approved_action": action,
        "reason": "Recovery recommendation satisfies the current safety policies.",
        "risk_flags": risk_flags
    }