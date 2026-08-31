def get_recovery_recommendation(payment):
    """
    RecoverAI Recovery Recommendation Engine

    Converts payment failure reasons into a structured
    recovery recommendation that can be consumed by
    the policy engine and action executor.

    The recovery engine recommends an action.
    The Policy Engine decides whether that action is allowed.
    """

    failure_reason = (payment.failure_reason or "").lower().strip()

    # ---------------------------------------------------------
    # INVALID PAYMENT ID
    # ---------------------------------------------------------

    if "invalid payment id" in failure_reason:
        return {
            "failure_category": "Invalid Payment ID",
            "recommended_action": "reject_request",
            "recommendation": (
                "Reject the recovery request because the payment ID "
                "is invalid."
            ),
            "success_probability": 0.0,
            "requires_human": False,
            "delay_minutes": 0
        }

    # ---------------------------------------------------------
    # DUPLICATE WEBHOOK
    # ---------------------------------------------------------

    if "duplicate webhook" in failure_reason:
        return {
            "failure_category": "Duplicate Webhook",
            "recommended_action": "ignore_duplicate",
            "recommendation": (
                "Ignore the duplicate webhook and keep the original "
                "payment record."
            ),
            "success_probability": 0.0,
            "requires_human": False,
            "delay_minutes": 0
        }

    # ---------------------------------------------------------
    # PAYMENT ALREADY CAPTURED
    # ---------------------------------------------------------

    if "already captured" in failure_reason:
        return {
            "failure_category": "Payment Already Captured",
            "recommended_action": "do_not_retry",
            "recommendation": (
                "Do not retry the payment. Verify the existing "
                "captured payment."
            ),
            "success_probability": 1.0,
            "requires_human": False,
            "delay_minutes": 0
        }

    # ---------------------------------------------------------
    # CUSTOMER OPTED OUT
    # ---------------------------------------------------------

    if "opted out" in failure_reason:
        return {
            "failure_category": "Customer Opted Out",
            "recommended_action": "do_not_retry",
            "recommendation": (
                "Do not retry automatically because the customer "
                "has opted out."
            ),
            "success_probability": 0.0,
            "requires_human": False,
            "delay_minutes": 0
        }

    # ---------------------------------------------------------
    # RETRY LIMIT EXCEEDED
    # ---------------------------------------------------------

    if "retry limit" in failure_reason:
        return {
            "failure_category": "Retry Limit Exceeded",
            "recommended_action": "require_human_review",
            "recommendation": (
                "Stop automatic retries and require manual review "
                "or another payment method."
            ),
            "success_probability": 0.2,
            "requires_human": True,
            "delay_minutes": 0
        }

    # ---------------------------------------------------------
    # HIGH-VALUE PAYMENT
    # ---------------------------------------------------------

    if "high-value" in failure_reason or "approval" in failure_reason:
        return {
            "failure_category": "High-Value Payment",
            "recommended_action": "require_human_review",
            "recommendation": (
                "Route the payment for approval before retrying."
            ),
            "success_probability": 0.5,
            "requires_human": True,
            "delay_minutes": 0
        }

    # ---------------------------------------------------------
    # LLM TIMEOUT
    # ---------------------------------------------------------

    if "llm timeout" in failure_reason:
        return {
            "failure_category": "LLM Timeout",
            "recommended_action": "retry_payment",
            "recommendation": (
                "Use the fallback recovery process and retry "
                "the payment diagnosis."
            ),
            "success_probability": 0.6,
            "requires_human": False,
            "delay_minutes": 5
        }

    # ---------------------------------------------------------
    # PAYMENT API UNAVAILABLE
    # ---------------------------------------------------------

    if "api unavailable" in failure_reason:
        return {
            "failure_category": "Payment Service Unavailable",
            "recommended_action": "retry_payment",
            "recommendation": (
                "Retry the payment after the payment service "
                "becomes available."
            ),
            "success_probability": 0.7,
            "requires_human": False,
            "delay_minutes": 5
        }

    # ---------------------------------------------------------
    # NETWORK CONNECTIVITY ISSUE
    # ---------------------------------------------------------

    if "network connectivity" in failure_reason:
        return {
            "failure_category": "Network Connectivity Issue",
            "recommended_action": "retry_payment",
            "recommendation": (
                "Check the network connection and retry the "
                "payment after connectivity is restored."
            ),
            "success_probability": 0.75,
            "requires_human": False,
            "delay_minutes": 5
        }

    # ---------------------------------------------------------
    # PAYMENT TIMEOUT
    # ---------------------------------------------------------

    if "timeout" in failure_reason or "timed out" in failure_reason:
        return {
            "failure_category": "Payment Timeout",
            "recommended_action": "retry_payment",
            "recommendation": (
                "Retry the payment after a short wait."
            ),
            "success_probability": 0.8,
            "requires_human": False,
            "delay_minutes": 5
        }

    # ---------------------------------------------------------
    # INSUFFICIENT FUNDS
    # ---------------------------------------------------------

    if "insufficient" in failure_reason or "balance" in failure_reason:
        return {
            "failure_category": "Insufficient Funds",
            "recommended_action": "retry_after_funds_added",
            "recommendation": (
                "Ask the customer to add funds and retry "
                "the payment."
            ),
            "success_probability": 0.65,
            "requires_human": False,
            "delay_minutes": 0
        }

    # ---------------------------------------------------------
    # EXPIRED CARD
    # ---------------------------------------------------------

    if "card expired" in failure_reason or "expired" in failure_reason:
        return {
            "failure_category": "Expired Card",
            "recommended_action": "ask_customer_to_update_payment_method",
            "recommendation": (
                "Ask the customer to update their card details "
                "or use another card."
            ),
            "success_probability": 0.7,
            "requires_human": False,
            "delay_minutes": 0
        }

    # ---------------------------------------------------------
    # BANK DECLINED
    # ---------------------------------------------------------

    if "declined" in failure_reason or "decline" in failure_reason:
        return {
            "failure_category": "Bank Declined",
            "recommended_action": "ask_customer_to_contact_bank",
            "recommendation": (
                "Ask the customer to contact their bank or "
                "use another payment method."
            ),
            "success_probability": 0.5,
            "requires_human": False,
            "delay_minutes": 0
        }

    # ---------------------------------------------------------
    # INVALID PAYMENT DETAILS
    # ---------------------------------------------------------

    if "invalid" in failure_reason:
        return {
            "failure_category": "Invalid Payment Details",
            "recommended_action": "ask_customer_to_update_payment_method",
            "recommendation": (
                "Ask the customer to verify the payment details "
                "and try again."
            ),
            "success_probability": 0.6,
            "requires_human": False,
            "delay_minutes": 0
        }

    # ---------------------------------------------------------
    # OTHER FAILURE
    # ---------------------------------------------------------

    if failure_reason:
        return {
            "failure_category": "Other Failure",
            "recommended_action": "retry_payment",
            "recommendation": (
                "Ask the customer to retry the payment or use "
                "another payment method."
            ),
            "success_probability": 0.5,
            "requires_human": False,
            "delay_minutes": 5
        }

    # ---------------------------------------------------------
    # UNKNOWN
    # ---------------------------------------------------------

    return {
        "failure_category": "Unknown",
        "recommended_action": "require_human_review",
        "recommendation": (
            "Unable to determine the failure reason. "
            "Manual review is required."
        ),
        "success_probability": 0.0,
        "requires_human": True,
        "delay_minutes": 0
    }