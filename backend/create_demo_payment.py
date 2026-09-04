from backend.database import SessionLocal
from backend.models import Customer, Payment

db = SessionLocal()

try:
    customer = Customer(
        name="RecoverAI Demo Customer",
        email="demo_customer@recoverai.test"
    )
    db.add(customer)
    db.flush()

    payment = Payment(
        customer_id=customer.id,
        amount=4999,
        currency="INR",
        status="failed",
        order_id="RECOVERAI-DEMO-4999",
        failure_reason="bank timeout"
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    print("DEMO PAYMENT CREATED")
    print("--------------------")
    print("Customer ID:", customer.id)
    print("Payment ID:", payment.id)
    print("Amount: ₹", payment.amount)
    print("Failure reason:", payment.failure_reason)
    print("Order ID:", payment.order_id)

finally:
    db.close()