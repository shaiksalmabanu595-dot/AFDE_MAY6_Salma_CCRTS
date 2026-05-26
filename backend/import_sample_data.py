"""
Import complaints_sample.csv into the CCRTS SQLite database.
Run from the backend/ directory:
    python import_sample_data.py
"""
import sys
import csv
import os
import sqlite3
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from app.database import DB_PATH
from app.utils.auth import hash_password

CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "datasets", "complaints_sample.csv")


def parse_dt(value):
    if not value or value.strip() == "":
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    return None


def dt_str(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else None


def main():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    cur = conn.cursor()

    try:
        # --- Ensure roles exist ---
        for r in ["Admin", "Agent", "Customer", "Supervisor"]:
            cur.execute("SELECT role_id FROM roles WHERE role_name=?", (r,))
            if not cur.fetchone():
                cur.execute("INSERT INTO roles (role_name) VALUES (?)", (r,))
        conn.commit()

        cur.execute("SELECT role_id FROM roles WHERE role_name='Customer'")
        customer_role_id = cur.fetchone()["role_id"]
        cur.execute("SELECT role_id FROM roles WHERE role_name='Agent'")
        agent_role_id = cur.fetchone()["role_id"]

        # --- Read CSV ---
        rows = []
        unique_categories = set()
        unique_customers = {}
        unique_agents = set()

        with open(CSV_PATH, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
                unique_categories.add(row["category"].strip())
                email = row["customer_email"].strip()
                unique_customers[email] = row["customer_name"].strip()
                if row["assigned_to"].strip():
                    unique_agents.add(row["assigned_to"].strip())

        # --- Seed missing categories ---
        cat_map = {}
        for cat_name in unique_categories:
            cur.execute("SELECT category_id FROM categories WHERE category_name=?", (cat_name,))
            row_db = cur.fetchone()
            if not row_db:
                cur.execute(
                    "INSERT INTO categories (category_name, description) VALUES (?, ?)",
                    (cat_name, f"Category: {cat_name}"),
                )
                conn.commit()
                cur.execute("SELECT category_id FROM categories WHERE category_name=?", (cat_name,))
                row_db = cur.fetchone()
            cat_map[cat_name] = row_db["category_id"]

        # --- Seed customer users ---
        customer_map = {}
        for email, name in unique_customers.items():
            cur.execute("SELECT user_id FROM users WHERE email=?", (email,))
            row_db = cur.fetchone()
            if not row_db:
                ph = hash_password("customer123")
                cur.execute(
                    "INSERT INTO users (name, email, password_hash, role_id) VALUES (?, ?, ?, ?)",
                    (name, email, ph, customer_role_id),
                )
                conn.commit()
                cur.execute("SELECT user_id FROM users WHERE email=?", (email,))
                row_db = cur.fetchone()
            customer_map[email] = row_db["user_id"]

        # --- Seed agent users from CSV agent codes ---
        agent_map = {}
        for agent_code in unique_agents:
            agent_email = f"{agent_code}@ccrts.com"
            cur.execute("SELECT user_id FROM users WHERE email=?", (agent_email,))
            row_db = cur.fetchone()
            if not row_db:
                ph = hash_password("agent123")
                cur.execute(
                    "INSERT INTO users (name, email, password_hash, role_id) VALUES (?, ?, ?, ?)",
                    (agent_code.capitalize(), agent_email, ph, agent_role_id),
                )
                conn.commit()
                cur.execute("SELECT user_id FROM users WHERE email=?", (agent_email,))
                row_db = cur.fetchone()
            agent_map[agent_code] = row_db["user_id"]

        # --- Import complaints ---
        imported = 0
        skipped = 0
        for row in rows:
            code = row["complaint_code"].strip()
            cur.execute("SELECT complaint_id FROM complaints WHERE complaint_code=?", (code,))
            if cur.fetchone():
                skipped += 1
                continue

            customer_email = row["customer_email"].strip()
            category_name = row["category"].strip()
            agent_code = row["assigned_to"].strip()
            status = row["status"].strip()
            resolved_at = parse_dt(row.get("resolved_at", ""))
            closed_at = resolved_at if status == "Closed" else None
            created_at = parse_dt(row.get("created_at", ""))

            cur.execute(
                """INSERT INTO complaints
                   (complaint_code, customer_id, category_id, assigned_to, title, description,
                    priority, status, sla_hours, created_at, resolved_at, closed_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    code,
                    customer_map[customer_email],
                    cat_map[category_name],
                    agent_map.get(agent_code) if agent_code else None,
                    row["title"].strip(),
                    row["title"].strip(),
                    row["priority"].strip(),
                    status,
                    int(row["sla_hours"]) if row["sla_hours"] else 48,
                    dt_str(created_at),
                    dt_str(resolved_at),
                    dt_str(closed_at),
                ),
            )
            complaint_id = cur.lastrowid

            # Import feedback if rating exists
            rating_str = row.get("feedback_rating", "").strip()
            if rating_str:
                try:
                    rating = int(float(rating_str))
                    if 1 <= rating <= 5:
                        cur.execute(
                            "INSERT INTO feedback (complaint_id, rating, comments) VALUES (?, ?, ?)",
                            (complaint_id, rating, row.get("resolution_comment", "").strip() or None),
                        )
                except ValueError:
                    pass

            imported += 1

        conn.commit()
        print(f"Done.")
        print(f"  Complaints imported : {imported}")
        print(f"  Complaints skipped  : {skipped}")
        print(f"  Categories added    : {len(unique_categories)}")
        print(f"  Customer accounts   : {len(unique_customers)}")
        print(f"  Agent accounts      : {len(unique_agents)}")

    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
