import sqlite3
import os
import time
import json
import re
from datetime import datetime


def init_db(db_path: str, data_dir: str):
    """Create the SQLite DB and required tables if not present."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS bills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            file_path TEXT,
            vendor TEXT,
            date TEXT,
            amount TEXT,
            category TEXT,
            raw_text TEXT,
            metadata TEXT,
            created_at TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            bill_id INTEGER,
            due_date TEXT,
            category TEXT,
            description TEXT,
            status TEXT DEFAULT 'active',
            created_at TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS shopping_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            quantity INTEGER DEFAULT 1,
            bought INTEGER DEFAULT 0,
            source_vendor TEXT,
            created_at TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def save_bill(db_path: str, uploaded_file, vendor: str, date_str: str, amount: str, category: str, raw_text: str, line_items=None):
    try:
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        timestamp = int(time.time())
        filename = f"receipt_{timestamp}_{uploaded_file.name}"
        data_dir = os.path.dirname(db_path)
        file_path = os.path.join(data_dir, filename)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getvalue())

        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        metadata = {"saved_by": "friendvault", "line_items": line_items or []}
        cur.execute(
            "INSERT INTO bills (filename, file_path, vendor, date, amount, category, raw_text, metadata, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (filename, file_path, vendor, date_str, amount, category, raw_text, json.dumps(metadata), time.strftime("%Y-%m-%d %H:%M:%S")),
        )
        rowid = cur.lastrowid
        conn.commit()
        conn.close()
        return rowid
    except Exception as e:
        print("save_bill error:", e)
        return None


def list_bills(db_path: str):
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute(
            "SELECT id, filename, vendor, date, amount, category, metadata, created_at FROM bills ORDER BY created_at DESC LIMIT 200"
        )
        rows = cur.fetchall()
        conn.close()
        result = []
        for r in rows:
            metadata = {}
            try:
                metadata = json.loads(r[6]) if r[6] else {}
            except Exception:
                metadata = {}
            result.append({
                "id": r[0],
                "file": r[1],
                "vendor": r[2],
                "date": r[3],
                "amount": r[4],
                "category": r[5],
                "metadata": metadata,
                "created_at": r[7],
            })
        return result
    except Exception as e:
        print("list_bills error:", e)
        return []


def sanitize_due_date(date_text: str):
    today = datetime.now()
    if not date_text:
        return today.strftime("%Y-%m-%d")
    try:
        dt = datetime.strptime(date_text, "%Y-%m-%d")
    except Exception:
        try:
            dt = datetime.fromisoformat(date_text)
        except Exception:
            return today.strftime("%Y-%m-%d")
    if dt.year < 2000 or dt > datetime(2035, 12, 31):
        return today.strftime("%Y-%m-%d")
    return dt.strftime("%Y-%m-%d")


def infer_due_date(date_text: str, category: str):
    return sanitize_due_date(date_text)


def save_reminder(db_path: str, title: str, bill_id: int, due_date: str, category: str, description: str, status: str = "active"):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO reminders (title, bill_id, due_date, category, description, status, created_at) VALUES (?,?,?,?,?,?,?)",
        (title, bill_id, due_date, category, description, status, time.strftime("%Y-%m-%d %H:%M:%S")),
    )
    conn.commit()
    conn.close()


def list_reminders(db_path: str):
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT id, title, bill_id, due_date, category, description, status FROM reminders ORDER BY due_date ASC LIMIT 200")
        rows = cur.fetchall()
        conn.close()
        return [
            {
                "id": r[0],
                "title": r[1],
                "bill_id": r[2],
                "due_date": r[3],
                "category": r[4],
                "description": r[5],
                "status": r[6],
            }
            for r in rows
        ]
    except Exception:
        return []


def update_reminder_due_date(db_path: str, reminder_id: int, new_due_date: str):
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("UPDATE reminders SET due_date = ? WHERE id = ?", (new_due_date, reminder_id))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def mark_reminder_paid(db_path: str, reminder_id: int):
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("UPDATE reminders SET status = 'paid' WHERE id = ?", (reminder_id,))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def set_reminder_status(db_path: str, reminder_id: int, status: str):
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("UPDATE reminders SET status = ? WHERE id = ?", (status, reminder_id))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def delete_bill(db_path: str, bill_id: int):
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT file_path FROM bills WHERE id = ?", (bill_id,))
        row = cur.fetchone()
        if row and row[0] and os.path.exists(row[0]):
            try:
                os.remove(row[0])
            except Exception:
                pass
        cur.execute("DELETE FROM reminders WHERE bill_id = ?", (bill_id,))
        cur.execute("DELETE FROM bills WHERE id = ?", (bill_id,))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def generate_reminder_from_bill(bill):
    vendor = (bill.get("vendor") or "Unknown bill").strip()
    category = (bill.get("category") or "Uncategorized").strip()
    date_text = bill.get("date") or datetime.now().strftime("%Y-%m-%d")
    amount = bill.get("amount") or "0"
    title = f"{vendor} payment"
    if "utility" in category.lower() or "electric" in category.lower():
        title = "Pay utilities bill"
    elif "rent" in category.lower():
        title = "Pay rent"
    elif "subscription" in category.lower() or "subscript" in category.lower():
        title = f"Subscription renewal: {vendor}"
    elif "groceries" in category.lower():
        title = f"Grocery restock: {vendor}"

    due_date = infer_due_date(date_text, category)
    description = f"{title} for {vendor}. Amount: {amount}."
    return {"title": title, "due_date": due_date, "category": category, "description": description}


def ensure_reminder_for_bill(db_path: str, bill):
    if not bill.get("vendor"):
        return None
    suggestion = generate_reminder_from_bill(bill)
    for rem in list_reminders(db_path):
        if rem["title"] == suggestion["title"] and str(rem["bill_id"]) == str(bill.get("id")):
            return None
    save_reminder(
        db_path,
        suggestion["title"],
        bill.get("id"),
        suggestion["due_date"],
        suggestion["category"],
        suggestion["description"],
        "active",
    )
    return suggestion


def generate_reminders_for_all_bills(db_path: str):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT id, vendor, date, amount, category FROM bills ORDER BY date DESC LIMIT 50")
    rows = cur.fetchall()
    conn.close()
    suggestions = []
    for row in rows:
        bill = {"id": row[0], "vendor": row[1], "date": row[2], "amount": row[3], "category": row[4]}
        suggestions.append(generate_reminder_from_bill(bill))
    return suggestions


def get_monthly_summary(db_path: str):
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute(
            "SELECT substr(date, 1, 7) AS month, COALESCE(SUM(CAST(amount AS REAL)), 0) AS total, COUNT(*) AS count FROM bills WHERE amount IS NOT NULL AND amount != '' GROUP BY substr(date, 1, 7) ORDER BY month DESC LIMIT 6"
        )
        rows = cur.fetchall()
        conn.close()
        return [{"month": r[0], "total": round(float(r[1] or 0), 2), "count": r[2]} for r in rows]
    except Exception:
        return []


def sync_shopping_items_from_bill(db_path: str, line_items, source_vendor: str = ""):
    if not line_items:
        return []
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    added = []
    for item in line_items:
        name = (item.get("name") or "").strip()
        if not name:
            continue
        name = name.rstrip(':').strip()
        if re.search(r"\b(gratuity|tip|service\s*charge|tax|total|subtotal|amount|balance)\b", name, re.I):
            continue
        existing = cur.execute("SELECT id FROM shopping_items WHERE LOWER(name) = LOWER(?) AND bought = 0 LIMIT 1", (name,)).fetchone()
        if not existing:
            cur.execute(
                "INSERT INTO shopping_items (name, quantity, bought, source_vendor, created_at) VALUES (?,?,?,?,?)",
                (name, 1, 0, source_vendor, time.strftime("%Y-%m-%d %H:%M:%S")),
            )
            added.append(name)
    conn.commit()
    conn.close()
    return added


def list_shopping_items(db_path: str):
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT id, name, quantity, bought, source_vendor FROM shopping_items ORDER BY bought ASC, name ASC")
        rows = cur.fetchall()
        conn.close()
        return [{
            "id": r[0],
            "name": r[1],
            "quantity": r[2],
            "bought": bool(r[3]),
            "source_vendor": r[4],
        } for r in rows]
    except Exception:
        return []


def toggle_shopping_item(db_path: str, item_id: int, bought: bool):
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("UPDATE shopping_items SET bought = ? WHERE id = ?", (1 if bought else 0, item_id))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False
