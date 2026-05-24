import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import csv

random.seed(42)
np.random.seed(42)

# Reference data matching CCRTS Phase 1
CATEGORIES = [
    "Billing & Payments", "Technical Support", "Service Outage",
    "Product Quality", "Delivery & Shipping", "Account Management",
    "Refund & Returns", "Network Issues", "App & Website",
    "Customer Service"
]

PRIORITIES = ["Low", "Medium", "High", "Critical"]
SLA_HOURS = {"Low": 72, "Medium": 48, "High": 24, "Critical": 4}

STATUSES = ["Open", "Assigned", "In Progress", "Resolved", "Closed", "Escalated"]
STATUS_WEIGHTS = [0.05, 0.08, 0.10, 0.35, 0.35, 0.07]

AGENTS = [
    "agent001", "agent002", "agent003", "agent004", "agent005",
    "agent006", "agent007", "agent008", "agent009", "agent010"
]

FIRST_NAMES = [
    "Priya","Rahul","Ananya","Vikram","Sneha","Arjun","Kavya","Rohan",
    "Divya","Kiran","Amit","Pooja","Suresh","Meena","Rajesh","Nisha",
    "Arun","Lakshmi","Ganesh","Sunita","Mohammed","Fatima","Ravi","Deepa",
    "Sanjay","Rekha","Vijay","Usha","Manoj","Asha","John","Mary",
    "David","Sarah","Michael","Emma","James","Olivia","Robert","Sophia"
]

LAST_NAMES = [
    "Kumar","Sharma","Patel","Singh","Reddy","Nair","Iyer","Gupta",
    "Joshi","Mehta","Shah","Verma","Das","Rao","Pillai","Menon",
    "Bose","Chatterjee","Mukherjee","Ghosh","Ali","Khan","Siddiqui",
    "Ahmed","Ansari","Smith","Jones","Williams","Brown","Taylor"
]

COMPLAINT_TITLES = {
    "Billing & Payments": [
        "Incorrect charge on my account", "Double billing issue",
        "Payment not reflected", "Unexpected deduction from account",
        "Wrong invoice amount", "Overcharged for service"
    ],
    "Technical Support": [
        "Unable to login to account", "Software not working properly",
        "Error message on application", "System crashes frequently",
        "Feature not functioning", "Integration failure"
    ],
    "Service Outage": [
        "Service completely down", "Intermittent service disruption",
        "Cannot access service since morning", "Total blackout of service",
        "Service unavailable in my area", "Frequent service drops"
    ],
    "Product Quality": [
        "Product defective on arrival", "Poor quality product received",
        "Product stopped working after 2 days", "Quality not as advertised",
        "Damaged product received", "Product specifications mismatch"
    ],
    "Delivery & Shipping": [
        "Order not delivered on time", "Wrong item delivered",
        "Package damaged during delivery", "Order missing from delivery",
        "Delivery address not found", "Order stuck in transit"
    ],
    "Account Management": [
        "Unable to update profile information", "Account locked unexpectedly",
        "Cannot change password", "Account details incorrect",
        "Subscription not activated", "Account merge issue"
    ],
    "Refund & Returns": [
        "Refund not processed after 7 days", "Return request rejected wrongly",
        "Partial refund received", "Refund amount incorrect",
        "Return pickup not scheduled", "Refund credited to wrong account"
    ],
    "Network Issues": [
        "Slow internet speed", "Frequent connection drops",
        "No network in my area", "High latency affecting work",
        "WiFi not working", "Network congestion during peak hours"
    ],
    "App & Website": [
        "App crashes on opening", "Website not loading",
        "Cannot complete purchase on website", "App update broke functionality",
        "Login page not responding", "Mobile app very slow"
    ],
    "Customer Service": [
        "Agent was rude and unhelpful", "Long wait times on support call",
        "Issue not resolved after multiple calls", "Misleading information given",
        "Callback promise not fulfilled", "Escalation request ignored"
    ]
}

RESOLUTION_COMMENTS = [
    "Issue identified and resolved. Root cause was a system configuration error.",
    "Problem fixed after escalation to technical team.",
    "Customer was guided through troubleshooting steps. Issue resolved.",
    "Refund processed successfully. Will reflect in 3-5 business days.",
    "Technical team deployed a fix. Service restored.",
    "Account updated as requested. Customer verified the changes.",
    "Replacement dispatched. Tracking number shared with customer.",
    "Issue escalated to senior team and resolved within SLA.",
    "Configuration updated on backend. Customer confirmed resolution.",
    "Compensation credit added to customer account as goodwill gesture."
]

def generate_complaints(n=10200):
    records = []
    start_date = datetime(2025, 5, 1)
    end_date = datetime(2026, 5, 24)
    date_range = (end_date - start_date).days

    for i in range(1, n + 1):
        # Basic info
        category = random.choice(CATEGORIES)
        priority = random.choices(PRIORITIES, weights=[0.30, 0.35, 0.25, 0.10])[0]
        sla_hours = SLA_HOURS[priority]
        status = random.choices(STATUSES, weights=STATUS_WEIGHTS)[0]

        # Customer
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        customer_name = f"{first} {last}"
        customer_email = f"{first.lower()}.{last.lower()}{random.randint(1,99)}@email.com"

        # Dates
        created_offset = random.randint(0, date_range)
        created_at = start_date + timedelta(days=created_offset,
                                             hours=random.randint(0,23),
                                             minutes=random.randint(0,59))

        # Agent assignment
        assigned_to = None
        assigned_at = None
        if status not in ["Open"]:
            assigned_to = random.choice(AGENTS)
            assigned_at = created_at + timedelta(hours=random.uniform(0.5, 8))

        # Resolution
        resolved_at = None
        resolution_time_hours = None
        resolution_comment = None
        sla_breached = False

        if status in ["Resolved", "Closed"]:
            # Some resolve within SLA, some breach it
            if random.random() < 0.25:  # 25% breach SLA
                resolution_hours = sla_hours * random.uniform(1.1, 3.0)
                sla_breached = True
            else:
                resolution_hours = sla_hours * random.uniform(0.1, 0.95)

            resolved_at = created_at + timedelta(hours=resolution_hours)
            resolution_time_hours = round(resolution_hours, 2)
            resolution_comment = random.choice(RESOLUTION_COMMENTS)
        elif status == "Escalated":
            # Escalated often means SLA breached
            sla_breached = random.random() < 0.70
        elif status in ["In Progress", "Assigned"]:
            # Check if already past SLA
            hours_open = (end_date - created_at).total_seconds() / 3600
            sla_breached = hours_open > sla_hours and random.random() < 0.40

        # Feedback (only for resolved/closed)
        feedback_rating = None
        if status in ["Resolved", "Closed"] and random.random() < 0.65:
            if sla_breached:
                feedback_rating = random.choices([1,2,3,4,5], weights=[0.25,0.30,0.25,0.15,0.05])[0]
            else:
                feedback_rating = random.choices([1,2,3,4,5], weights=[0.05,0.10,0.20,0.35,0.30])[0]

        # Complaint code
        complaint_code = f"CMP-{created_at.year}-{i:05d}"

        # Title
        title = random.choice(COMPLAINT_TITLES[category])

        # Introduce intentional ETL noise (5%)
        if random.random() < 0.03:
            priority = priority.upper()  # casing noise
        if random.random() < 0.02:
            category = "  " + category  # whitespace noise
        if random.random() < 0.025:
            resolution_time_hours = -1  # invalid value for ETL to catch
        if random.random() < 0.02:
            feedback_rating = 0 if feedback_rating else None  # invalid rating

        records.append({
            "complaint_id": i,
            "complaint_code": complaint_code,
            "customer_name": customer_name,
            "customer_email": customer_email,
            "category": category,
            "priority": priority,
            "status": status,
            "title": title,
            "sla_hours": sla_hours,
            "sla_breached": sla_breached,
            "assigned_to": assigned_to,
            "assigned_at": assigned_at.strftime("%Y-%m-%d %H:%M:%S") if assigned_at else None,
            "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "resolved_at": resolved_at.strftime("%Y-%m-%d %H:%M:%S") if resolved_at else None,
            "resolution_time_hours": resolution_time_hours,
            "resolution_comment": resolution_comment,
            "feedback_rating": feedback_rating,
        })

    # Add ~200 exact duplicates for ETL dedup testing
    duplicates = random.sample(records[:5000], 200)
    for d in duplicates:
        dup = d.copy()
        records.append(dup)

    random.shuffle(records)
    return records

records = generate_complaints(10200)
df = pd.DataFrame(records)
df.to_csv("/home/claude/complaints_sample.csv", index=False)
print(f"Generated {len(df)} records")
print(f"Columns: {list(df.columns)}")
print(f"\nStatus distribution:")
print(df['status'].value_counts())
print(f"\nPriority distribution:")
print(df['priority'].value_counts())
print(f"\nSLA breached: {df['sla_breached'].sum()} ({df['sla_breached'].mean()*100:.1f}%)")
print(f"Duplicates to remove: ~200")
print(f"Invalid resolution times: {(df['resolution_time_hours'] < 0).sum()}")
