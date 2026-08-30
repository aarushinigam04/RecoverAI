import os
import razorpay
from dotenv import load_dotenv

load_dotenv()

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
    raise RuntimeError("Razorpay test API keys are missing from .env")

client = razorpay.Client(
    auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)
)


def create_test_order(amount: int = 100):
    """
    Creates a Razorpay Test Mode order.

    Amount is specified in paise.
    Example: 10000 paise = ₹100.
    """

    order_data = {
        "amount": amount,
        "currency": "INR",
        "receipt": "recoverai_test_order",
    }

    order = client.order.create(data=order_data)

    return order