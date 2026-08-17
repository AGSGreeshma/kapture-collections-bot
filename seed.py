from database import engine, SessionLocal, Base
from models import Customer

# Create the table if it doesn't exist
Base.metadata.create_all(bind=engine)

db = SessionLocal()

customers = [
    Customer(
        customer_id="CUST001",
        name="Rahul Sharma",
        phone="TEST-PHONE-001",
        loan_type="Personal Loan",
        overdue_amount=8499,
        days_past_due=12,
        payment_status="OVERDUE",
        verification_code="TEST-RAHUL-123",
    ),
    Customer(
        customer_id="CUST002",
        name="Priya Nair",
        phone="TEST-PHONE-002",
        loan_type="Two-Wheeler Loan",
        overdue_amount=4250,
        days_past_due=5,
        payment_status="OVERDUE",
        verification_code="TEST-PRIYA-456",
    ),
    Customer(
        customer_id="CUST003",
        name="Arjun Mehta",
        phone="TEST-PHONE-003",
        loan_type="Credit Card Loan",
        overdue_amount=15200,
        days_past_due=30,
        payment_status="OVERDUE",
        verification_code="TEST-ARJUN-789",
    ),
]

for c in customers:
    db.merge(c)  # merge = insert or update, safe to re-run

db.commit()
db.close()

print("Seeded 3 customers successfully.")