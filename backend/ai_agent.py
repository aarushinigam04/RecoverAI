def diagnose_payment(context):
    """
    AI Diagnosis Agent for RecoverAI.

    Analyzes structured payment context and returns
    a bounded, auditable recovery recommendation.

    The diagnosis layer is responsible for:
        1. Failure classification
        2. Recovery recommendation
        3. Confidence estimation
        4. Recovery probability estimation
        5. Risk flag generation

    Safety-critical decisions remain enforced by policy_engine.py.
    """

    payment = context["payment"]

    failure_reason = (
        payment.get("failure_reason") or ""
    ).lower().strip()

    amount = payment.get("amount") or 0

    payment_history = context.get(
        "payment_history",
        []
    )

    attempt_history = context.get(
        "attempt_history",
        []
    )

    recovery_history = context.get(
        "recovery_history",
        []
    )

    # =========================================================
    # DIAGNOSE PAYMENT FAILURE
    # =========================================================

    # ---------------------------------------------------------
    # FRAUD
    # ---------------------------------------------------------

    if "fraud" in failure_reason:

        category = "Fraud Detected"

        reason = (
            "The payment has been flagged as potentially "
            "fraudulent and must not be automatically recovered."
        )

        confidence = 0.99

        action = "do_not_retry"

        delay_minutes = 0

        success_probability = 0.0

    # ---------------------------------------------------------
    # CUSTOMER OPTED OUT
    # ---------------------------------------------------------

    elif (
        "customer opted out" in failure_reason
        or "opted out" in failure_reason
    ):

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
    # PAYMENT ALREADY CAPTURED
    # ---------------------------------------------------------

    elif "already captured" in failure_reason:

        category = "Payment Already Captured"

        reason = (
            "The payment appears to have already been captured. "
            "A retry would create an unsafe duplicate payment risk."
        )

        confidence = 0.99

        action = "do_not_retry"

        delay_minutes = 0

        success_probability = 0.0

    # ---------------------------------------------------------
    # DUPLICATE EVENT / WEBHOOK
    # ---------------------------------------------------------

    elif (
        "duplicate webhook" in failure_reason
        or "duplicate event" in failure_reason
    ):

        category = "Duplicate Event"

        reason = (
            "The payment event appears to be a duplicate event "
            "and should not trigger another payment attempt."
        )

        confidence = 0.99

        action = "do_not_retry"

        delay_minutes = 0

        success_probability = 0.0

    # ---------------------------------------------------------
    # RETRY LIMIT
    # ---------------------------------------------------------

    elif (
        "retry limit" in failure_reason
        or "retry limit exceeded" in failure_reason
    ):

        category = "Retry Limit Exceeded"

        reason = (
            "The payment has exceeded the permitted retry limit. "
            "Further automatic recovery is prohibited."
        )

        confidence = 0.99

        action = "require_human_review"

        delay_minutes = 0

        success_probability = 0.0

    # ---------------------------------------------------------
    # HIGH VALUE
    # ---------------------------------------------------------

    elif (
        amount >= 50000
        or "high-value" in failure_reason
        or "high value" in failure_reason
    ):

        category = "High-Value Payment"

        reason = (
            "The payment requires additional review because "
            "of its high-value nature."
        )

        confidence = 0.99

        action = "require_human_review"

        delay_minutes = 0

        success_probability = 0.0

    # ---------------------------------------------------------
    # INSUFFICIENT FUNDS
    # ---------------------------------------------------------

    elif (
        "insufficient funds" in failure_reason
        or "insufficient" in failure_reason
        or "funds unavailable" in failure_reason
        or "not enough funds" in failure_reason
    ):

        category = "Insufficient Funds"

        reason = (
            "The payment appears to have failed because "
            "sufficient funds were unavailable."
        )

        confidence = 0.95

        action = "ask_customer_to_update_payment_method"

        delay_minutes = 30

        success_probability = 0.65

    # ---------------------------------------------------------
    # CARD EXPIRED
    # ---------------------------------------------------------

    elif (
        "card expired" in failure_reason
        or "expired card" in failure_reason
        or "expired" in failure_reason
    ):

        category = "Card Expired"

        reason = (
            "The payment method appears to have expired. "
            "The customer should update the payment method."
        )

        confidence = 0.96

        action = (
            "ask_customer_to_update_payment_method"
        )

        delay_minutes = 0

        success_probability = 0.65

    # ---------------------------------------------------------
    # INVALID PAYMENT DETAILS
    # ---------------------------------------------------------

    elif (
        "invalid payment details" in failure_reason
        or "incorrect cvv" in failure_reason
        or "invalid card" in failure_reason
        or "invalid payment details" in failure_reason
    ):

        category = "Invalid Payment Details"

        reason = (
            "The supplied payment details appear to be invalid "
            "and should be corrected before another attempt."
        )

        confidence = 0.95

        action = (
            "ask_customer_to_update_payment_method"
        )

        delay_minutes = 0

        success_probability = 0.60

    # ---------------------------------------------------------
    # BANK DECLINED
    # ---------------------------------------------------------

    elif (
        "bank declined" in failure_reason
        or "declined by bank" in failure_reason
        or "declined" in failure_reason
        or "decline" in failure_reason
    ):

        category = "Bank Declined"

        reason = (
            "The customer's bank appears to have declined "
            "the payment. A controlled retry may succeed "
            "after the decline condition is resolved."
        )

        confidence = 0.92

        action = "ask_customer_to_update_payment_method"

        delay_minutes = 15

        success_probability = 0.60

    # ---------------------------------------------------------
    # BANK TIMEOUT
    # ---------------------------------------------------------

    elif (
        "bank timeout" in failure_reason
        or "bank timed out" in failure_reason
    ):

        category = "Bank Timeout"

        reason = (
            "The banking service appears to have timed out "
            "while processing the payment."
        )

        confidence = 0.94

        action = "retry_payment"

        delay_minutes = 10

        success_probability = 0.80

    # ---------------------------------------------------------
    # GATEWAY TIMEOUT
    # ---------------------------------------------------------

    elif (
        "gateway timeout" in failure_reason
        or "gateway timed out" in failure_reason
    ):

        category = "Gateway Timeout"

        reason = (
            "The payment gateway appears to have timed out "
            "during processing."
        )

        confidence = 0.94

        action = "retry_payment"

        delay_minutes = 10

        success_probability = 0.80

    # ---------------------------------------------------------
    # PAYMENT API UNAVAILABLE
    # ---------------------------------------------------------

    elif (
        "payment api unavailable" in failure_reason
        or "api unavailable" in failure_reason
    ):

        category = "Payment api Unavailable"

        reason = (
            "The payment service was temporarily unavailable. "
            "A delayed retry should be used instead of repeated "
            "immediate requests."
        )

        confidence = 0.96

        action = "retry_payment"

        delay_minutes = 15

        success_probability = 0.80

    # ---------------------------------------------------------
    # NETWORK TIMEOUT
    # ---------------------------------------------------------

    elif (
        "network timeout" in failure_reason
        or "network timed out" in failure_reason
    ):

        category = "Network Timeout"

        reason = (
            "The payment attempt appears to have failed because "
            "of a network timeout."
        )

        confidence = 0.94

        action = "retry_payment"

        delay_minutes = 10

        success_probability = 0.80

    # ---------------------------------------------------------
    # NETWORK CONNECTIVITY
    # ---------------------------------------------------------

    elif (
        "network connectivity" in failure_reason
        or "connectivity issue" in failure_reason
        or "network error" in failure_reason
    ):

        category = "Network Connectivity Issue"

        reason = (
            "The payment could not be completed because of "
            "a network connectivity problem."
        )

        confidence = 0.93

        action = "retry_payment"

        delay_minutes = 10

        success_probability = 0.80

    # ---------------------------------------------------------
    # LLM TIMEOUT
    # ---------------------------------------------------------

    elif "llm timeout" in failure_reason:

        category = "LLM Timeout"

        reason = (
            "The AI diagnosis service timed out. "
            "A bounded fallback recovery process should be used."
        )

        confidence = 0.95

        action = "retry_payment"

        delay_minutes = 10

        success_probability = 0.60

    # ---------------------------------------------------------
    # INVALID PAYMENT ID
    # ---------------------------------------------------------

    elif "invalid payment id" in failure_reason:

        category = "Invalid Payment ID"

        reason = (
            "The payment identifier provided for the transaction "
            "appears to be invalid."
        )

        confidence = 0.99

        action = "require_human_review"

        delay_minutes = 0

        success_probability = 0.0

    # ---------------------------------------------------------
    # OTHER FAILURE
    # ---------------------------------------------------------

    else:

        category = "Other Failure"

        reason = (
            "The payment failure reason could not be confidently "
            "mapped to a known recovery category."
        )

        confidence = 0.50

        action = "require_human_review"

        delay_minutes = 15

        success_probability = 0.0

    # =========================================================
    # RISK ASSESSMENT
    # =========================================================

    risk_flags = []

    # ---------------------------------------------------------
    # HIGH VALUE
    # ---------------------------------------------------------

    if amount >= 50000:

        risk_flags.append(
            "high_value_payment"
        )

    # ---------------------------------------------------------
    # MULTIPLE ATTEMPTS
    # ---------------------------------------------------------

    if len(attempt_history) >= 3:

        risk_flags.append(
            "multiple_payment_attempts"
        )

    # ---------------------------------------------------------
    # PREVIOUS FAILURES
    # ---------------------------------------------------------

    failed_previous_payments = sum(
        1
        for p in payment_history
        if p.get("status") == "failed"
    )

    successful_previous_payments = sum(
        1
        for p in payment_history
        if p.get("status")
        in ["success", "captured", "paid"]
    )

    if failed_previous_payments >= 3:

        risk_flags.append(
            "repeated_payment_failures"
        )

    # ---------------------------------------------------------
    # PREVIOUS RECOVERY
    # ---------------------------------------------------------

    if recovery_history:

        risk_flags.append(
            "previous_recovery_case"
        )

    # ---------------------------------------------------------
    # RESTRICTED ACTION
    # ---------------------------------------------------------

    if action in [
        "do_not_retry",
        "require_human_review"
    ]:

        risk_flags.append(
            "restricted_recovery_action"
        )

    # ---------------------------------------------------------
    # FRAUD
    # ---------------------------------------------------------

    if category == "Fraud Detected":

        if "fraud_detected" not in risk_flags:

            risk_flags.append(
                "fraud_detected"
            )

    # =========================================================
    # LOW CONFIDENCE SAFETY ESCALATION
    # =========================================================

    if confidence < 0.60:

        action = "require_human_review"

        requires_human = True

        if "low_diagnostic_confidence" not in risk_flags:

            risk_flags.append(
                "low_diagnostic_confidence"
            )

    else:

        requires_human = (
            action == "require_human_review"
        )

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

            f"The payment was classified as "
            f"'{category}' with "
            f"{confidence:.0%} diagnostic confidence. "

            f"The recommendation considers "
            f"{successful_previous_payments} previous "
            f"successful payments and "
            f"{failed_previous_payments} previous "
            f"failed payments."
        )
    }