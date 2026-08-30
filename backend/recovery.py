def get_recovery_recommendation(payment):
    failure_reason = (payment.failure_reason or "").lower().strip()

    # ---------------------------------------------------------
    # INVALID PAYMENT ID
    # ---------------------------------------------------------

    if "invalid payment id" in failure_reason:
        return {
            "failure_category": "Invalid Payment ID",
            "recommendation": "Reject the recovery request because the payment ID is invalid."
        }

    # ---------------------------------------------------------
    # NETWORK CONNECTIVITY ISSUE
    # ---------------------------------------------------------

    elif "network connectivity" in failure_reason:
        return {
            "failure_category": "Network Connectivity Issue",
            "recommendation": "Check the network connection and retry the payment after connectivity is restored."
        }

    # ---------------------------------------------------------
    # LLM TIMEOUT
    # ---------------------------------------------------------

    elif "llm timeout" in failure_reason:
        return {
            "failure_category": "LLM Timeout",
            "recommendation": "Use the fallback recovery process and retry the payment diagnosis."
        }

    # ---------------------------------------------------------
    # INSUFFICIENT FUNDS
    # ---------------------------------------------------------

    elif "insufficient" in failure_reason or "balance" in failure_reason:
        return {
            "failure_category": "Insufficient Funds",
            "recommendation": "Ask the customer to add funds and retry the payment."
        }

    # ---------------------------------------------------------
    # PAYMENT TIMEOUT
    # ---------------------------------------------------------

    elif "timeout" in failure_reason or "timed out" in failure_reason:
        return {
            "failure_category": "Payment Timeout",
            "recommendation": "Ask the customer to retry the payment after a short wait."
        }

    # ---------------------------------------------------------
    # INVALID PAYMENT DETAILS
    # ---------------------------------------------------------

    elif "invalid" in failure_reason:
        return {
            "failure_category": "Invalid Payment Details",
            "recommendation": "Ask the customer to verify the payment details and try again."
        }

    # ---------------------------------------------------------
    # HIGH-VALUE PAYMENT
    # ---------------------------------------------------------

    elif "high-value" in failure_reason or "approval" in failure_reason:
        return {
            "failure_category": "High-Value Payment",
            "recommendation": "Route the payment for approval before retrying."
        }

    # ---------------------------------------------------------
    # BANK DECLINED
    # ---------------------------------------------------------

    elif "declined" in failure_reason or "decline" in failure_reason:
        return {
            "failure_category": "Bank Declined",
            "recommendation": "Ask the customer to contact their bank or use another payment method."
        }

    # ---------------------------------------------------------
    # EXPIRED CARD
    # ---------------------------------------------------------

    elif "card expired" in failure_reason or "expired" in failure_reason:
        return {
            "failure_category": "Expired Card",
            "recommendation": "Ask the customer to update their card details or use another card."
        }

    # ---------------------------------------------------------
    # DUPLICATE WEBHOOK
    # ---------------------------------------------------------

    elif "duplicate webhook" in failure_reason:
        return {
            "failure_category": "Duplicate Webhook",
            "recommendation": "Ignore the duplicate webhook and keep the original payment record."
        }

    # ---------------------------------------------------------
    # PAYMENT API UNAVAILABLE
    # ---------------------------------------------------------

    elif "api unavailable" in failure_reason:
        return {
            "failure_category": "Payment Service Unavailable",
            "recommendation": "Retry the payment after the payment service becomes available."
        }

    # ---------------------------------------------------------
    # PAYMENT ALREADY CAPTURED
    # ---------------------------------------------------------

    elif "already captured" in failure_reason:
        return {
            "failure_category": "Payment Already Captured",
            "recommendation": "Do not retry the payment. Verify the existing captured payment."
        }

    # ---------------------------------------------------------
    # RETRY LIMIT EXCEEDED
    # ---------------------------------------------------------

    elif "retry limit" in failure_reason:
        return {
            "failure_category": "Retry Limit Exceeded",
            "recommendation": "Stop automatic retries and require manual review or another payment method."
        }

    # ---------------------------------------------------------
    # CUSTOMER OPTED OUT
    # ---------------------------------------------------------

    elif "opted out" in failure_reason:
        return {
            "failure_category": "Customer Opted Out",
            "recommendation": "Do not retry automatically because the customer has opted out."
        }

    # ---------------------------------------------------------
    # OTHER FAILURE
    # ---------------------------------------------------------

    elif failure_reason:
        return {
            "failure_category": "Other Failure",
            "recommendation": "Ask the customer to retry the payment or use another payment method."
        }

    # ---------------------------------------------------------
    # UNKNOWN
    # ---------------------------------------------------------

    else:
        return {
            "failure_category": "Unknown",
            "recommendation": "Unable to determine the failure reason."
        }
