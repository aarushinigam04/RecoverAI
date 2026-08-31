def diagnose_payment(context):
    """
    AI Diagnosis Agent for RecoverAI.

    Analyzes structured payment context and returns
    a bounded, auditable recovery recommendation.
    """

    payment = context["payment"]

    failure_reason = (payment.get("failure_reason") or "").lower().strip()
    amount = payment.get("amount") or 0

    payment_history = context.get("payment_history", [])
    attempt_history = context.get("attempt_history", [])
    recovery_history = context.get("recovery_history", [])

    # =========================================================
    # DIAGNOSE PAYMENT FAILURE
    # =========================================================

    # ---------------------------------------------------------
    # INSUFFICIENT FUNDS
    # ---------------------------------------------------------

    if "insufficient" in failure_reason or "fund" in failure_reason:
        category = "Insufficient Funds"
        reason = (
            "The payment appears to have failed because "
            "sufficient funds were unavailable."
        )
        confidence = 0.95
        action = "retry_after_funds_added"
        delay_minutes = 30
        success_probability = 0.75

    # ---------------------------------------------------------
    # INVALID PAYMENT DETAILS
    # ---------------------------------------------------------

    elif (
        "expired" in failure_reason
        or "invalid payment details" in failure_reason
        or "invalid payment id" in failure_reason
        or "incorrect cvv" in failure_reason
        or "invalid card" in failure_reason
    ):
        category = "Invalid Payment Details"

        if "expired" in failure_reason:
            reason = "The payment method appears to have expired."
        elif "invalid payment id" in failure_reason:
            reason = (
                "The payment identifier provided for the transaction "
                "appears to be invalid."
            )
        elif "incorrect cvv" in failure_reason:
            reason = (
                "The card verification information appears to be incorrect."
            )
        elif "invalid card" in failure_reason:
            reason = (
                "The provided card information appears to be invalid."
            )
        else:
            reason = (
                "The supplied payment details appear to be invalid."
            )

        confidence = 0.95
        action = "ask_customer_to_update_payment_method"
        delay_minutes = 0
        success_probability = 0.35

    # ---------------------------------------------------------
    # BANK DECLINED
    # ---------------------------------------------------------

    elif "declined" in failure_reason or "decline" in failure_reason:
        category = "Bank Declined"
        reason = (
            "The customer's bank appears to have declined the payment."
        )
        confidence = 0.92
        action = "ask_customer_to_contact_bank"
        delay_minutes = 0
        success_probability = 0.40

    # ---------------------------------------------------------
    # PAYMENT / NETWORK TIMEOUT
    # ---------------------------------------------------------

    elif "timeout" in failure_reason or "timed out" in failure_reason:
        category = "Payment Timeout"
        reason = (
            "The payment attempt appears to have timed out."
        )
        confidence = 0.94
        action = "retry_payment"
        delay_minutes = 5
        success_probability = 0.70

    # ---------------------------------------------------------
    # NETWORK CONNECTIVITY
    # ---------------------------------------------------------

    elif "network connectivity" in failure_reason:
        category = "Network Connectivity Issue"
        reason = (
            "The payment could not be completed because of a "
            "network connectivity issue."
        )
        confidence = 0.93
        action = "retry_payment"
        delay_minutes = 10
        success_probability = 0.70

    # ---------------------------------------------------------
    # PAYMENT API UNAVAILABLE
    # ---------------------------------------------------------

    elif "api unavailable" in failure_reason:
        category = "Payment Service Unavailable"
        reason = (
            "The payment service was temporarily unavailable."
        )
        confidence = 0.96
        action = "retry_payment"
        delay_minutes = 10
        success_probability = 0.80

    # ---------------------------------------------------------
    # LLM TIMEOUT
    # ---------------------------------------------------------

    elif "llm timeout" in failure_reason:
        category = "LLM Timeout"
        reason = (
            "The AI diagnosis service timed out, so the "
            "fallback recovery process should be used."
        )
        confidence = 0.95
        action = "retry_payment"
        delay_minutes = 10
        success_probability = 0.60

    # ---------------------------------------------------------
    # PAYMENT ALREADY CAPTURED
    # ---------------------------------------------------------

    elif "already captured" in failure_reason:
        category = "Payment Already Captured"
        reason = (
            "The payment appears to have already been captured."
        )
        confidence = 0.99
        action = "do_not_retry"
        delay_minutes = 0
        success_probability = 0.0

    # ---------------------------------------------------------
    # DUPLICATE WEBHOOK
    # ---------------------------------------------------------

    elif "duplicate webhook" in failure_reason:
        category = "Duplicate Event"
        reason = (
            "The payment event appears to be a duplicate webhook."
        )
        confidence = 0.99
        action = "do_not_retry"
        delay_minutes = 0
        success_probability = 0.0

    # ---------------------------------------------------------
    # RETRY LIMIT EXCEEDED
    # ---------------------------------------------------------

    elif "retry limit" in failure_reason:
        category = "Retry Limit Exceeded"
        reason = (
            "The payment has exceeded the permitted retry limit."
        )
        confidence = 0.99
        action = "require_human_review"
        delay_minutes = 0
        success_probability = 0.10

    # ---------------------------------------------------------
    # FRAUD DETECTED
    # ---------------------------------------------------------

    elif "fraud" in failure_reason:
        category = "Fraud Detected"
        reason = (
            "The payment has been flagged as potentially fraudulent "
            "and must not be automatically retried."
        )
        confidence = 0.99
        action = "do_not_retry"
        delay_minutes = 0
        success_probability = 0.0

    # ---------------------------------------------------------
    # CUSTOMER OPTED OUT
    # ---------------------------------------------------------

    elif "customer opted out" in failure_reason or "opted out" in failure_reason:
        category = "Customer Opted Out"
        reason = (
            "The customer has opted out of further payment "
            "recovery attempts."
        )
        confidence = 0.99
        action = "do_not_retry"
        delay_minutes = 0
        success_probability = 0.0

    # ---------------------------------------------------------
    # HIGH-VALUE PAYMENT
    # ---------------------------------------------------------

    elif "high-value" in failure_reason or "approval" in failure_reason:
        category = "High-Value Payment"
        reason = (
            "The payment requires additional review because "
            "of its high-value nature."
        )
        confidence = 0.90
        action = "require_human_review"
        delay_minutes = 0
        success_probability = 0.50

    # ---------------------------------------------------------
    # OTHER FAILURE
    # ---------------------------------------------------------

    else:
        category = "Other Failure"
        reason = (
            "The payment failure reason could not be confidently "
            "mapped to a known category."
        )
        confidence = 0.50
        action = "retry_payment"
        delay_minutes = 15
        success_probability = 0.40

    # =========================================================
    # RISK ASSESSMENT
    # =========================================================

    risk_flags = []

    # Keep this aligned with the Policy Engine threshold.
    if amount >= 50000:
        risk_flags.append("high_value_payment")

    if len(attempt_history) >= 3:
        risk_flags.append("multiple_payment_attempts")

    failed_previous_payments = sum(
        1
        for p in payment_history
        if p.get("status") == "failed"
    )

    successful_previous_payments = sum(
        1
        for p in payment_history
        if p.get("status") in ["success", "captured", "paid"]
    )

    if failed_previous_payments >= 3:
        risk_flags.append("repeated_payment_failures")

    if recovery_history:
        risk_flags.append("previous_recovery_case")

    if action in ["do_not_retry", "require_human_review"]:
        risk_flags.append("restricted_recovery_action")

    # Fraud gets an explicit risk flag.
    if category == "Fraud Detected":
        risk_flags.append("fraud_detected")

    # =========================================================
    # LOW CONFIDENCE SAFETY ESCALATION
    # =========================================================

    if confidence < 0.60:
        action = "require_human_review"
        requires_human = True

        if "low_diagnostic_confidence" not in risk_flags:
            risk_flags.append("low_diagnostic_confidence")
    else:
        requires_human = action == "require_human_review"

    # =========================================================
    # EXPECTED RECOVERY
    # =========================================================

    expected_recovery = round(
        amount * success_probability,
        2
    )

    # =========================================================
    # FINAL AUDITABLE RESPONSE
    # =========================================================

    return {
        "diagnosis": {
            "category": category,
            "reason": reason,
            "confidence": confidence
        },

        "recovery": {
            "recommended_action": action,
            "delay_minutes": delay_minutes,
            "success_probability": success_probability,
            "expected_recovery": expected_recovery
        },

        "risk_flags": risk_flags,

        "requires_human": requires_human,

        "explanation": (
            f"The payment was classified as '{category}' "
            f"with {confidence:.0%} diagnostic confidence. "
            f"The recommendation considers "
            f"{successful_previous_payments} previous successful payments "
            f"and {failed_previous_payments} previous failed payments."
        )
    }