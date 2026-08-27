def get_recovery_recommendation(payment):
    failure_reason = getattr(payment, "failure_reason", "")

    if not failure_reason:
        return {
            "action": "retry_payment",
            "message": "Payment failed. Customer can retry the payment."
        }

    reason = failure_reason.lower()

    # Invalid payment ID
    if "invalid payment id" in reason:
        return {
            "action": "reject_request",
            "message": "The payment ID is invalid. Please provide a valid payment ID."
        }

    # Duplicate webhook
    elif "duplicate webhook" in reason:
        return {
            "action": "ignore_duplicate",
            "message": "Duplicate webhook detected. No additional recovery action is required."
        }

    # LLM timeout
    elif "llm timeout" in reason:
        return {
            "action": "fallback_recovery",
            "message": "AI service timed out. Using the fallback recovery strategy."
        }

    # Payment API unavailable
    elif "payment api unavailable" in reason:
        return {
            "action": "retry_later",
            "message": "Payment service is temporarily unavailable. Retry the payment later."
        }

    # Payment already captured
    elif "payment already captured" in reason:
        return {
            "action": "no_action",
            "message": "Payment has already been captured. No retry is required."
        }

    # Retry limit exceeded
    elif "retry limit exceeded" in reason:
        return {
            "action": "contact_support",
            "message": "The maximum number of payment retries has been reached. Contact support."
        }

    # Customer opted out
    elif "customer opted out" in reason:
        return {
            "action": "do_not_retry",
            "message": "Customer has opted out of payment recovery. No automated retry will be attempted."
        }

    # High-value payment requiring approval
    elif "high-value payment requiring approval" in reason:
        return {
            "action": "require_approval",
            "message": "This high-value payment requires additional approval before recovery."
        }

    # Existing payment failure scenarios
    elif "insufficient" in reason or "balance" in reason:
        return {
            "action": "try_another_method",
            "message": "Insufficient funds. Customer should try another payment method."
        }

    elif "expired" in reason:
        return {
            "action": "update_card",
            "message": "The card appears to be expired. Customer should update the card details."
        }

    elif "declined" in reason:
        return {
            "action": "retry_payment",
            "message": "Payment was declined. Customer can retry or use another payment method."
        }

    elif "network" in reason or "timeout" in reason or "temporary" in reason:
        return {
            "action": "retry_later",
            "message": "A temporary payment issue occurred. Customer should retry after a short time."
        }

    elif "invalid" in reason:
        return {
            "action": "update_payment_details",
            "message": "Payment details appear to be invalid. Customer should check and update them."
        }

    else:
        return {
            "action": "contact_support",
            "message": "Payment failed for an unknown reason. Customer should contact support."
        }