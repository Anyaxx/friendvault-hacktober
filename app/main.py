import streamlit as st
from PIL import Image, ImageOps
import io
import os
import sys
import subprocess
import shutil
from datetime import datetime

if __package__ in (None, ""):
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import ocr as ocr_utils
from app import db as db_utils

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "friendvault.db")
os.makedirs(DATA_DIR, exist_ok=True)

db_utils.init_db(DB_PATH, DATA_DIR)


def trigger_local_notification(title: str, message: str):
    try:
        if sys.platform == "darwin":
            subprocess.run(['osascript', '-e', f'display notification "{message}" with title "{title}"'], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
        if shutil.which('notify-send'):
            subprocess.run(['notify-send', title, message], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


st.set_page_config(page_title="FriendVault", page_icon="🧾", layout="wide", initial_sidebar_state="collapsed")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&display=swap');
    [data-testid="stHeader"] { background: rgba(0,0,0,0); box-shadow: none; }
    [data-testid="stToolbar"] { display: none !important; }
    [data-testid="stSidebar"] { display: none !important; }
    section[data-testid="stSidebar"] { display: none !important; }
    html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
        background: #f3f4f6;
        color: #111111;
        font-family: 'IBM Plex Mono', monospace;
    }
    .block-container { padding-top: 1.8rem; padding-bottom: 2rem; }
    .hero {
        background: linear-gradient(135deg, #ffffff 0%, #edf5ff 100%);
        border: 1px solid rgba(17,17,17,0.08);
        border-radius: 22px;
        padding: 1.2rem 1.5rem;
        box-shadow: 0 8px 24px rgba(17,17,17,0.06);
        margin-bottom: 1.2rem;
    }
    .hero h1 { margin: 0; font-size: 2.3rem; color: #111111; }
    .hero p { margin-top: 0.45rem; color: #546170; font-size: 0.95rem; line-height: 1.6; }
    .metric {
        background: #ffffff;
        border: 1px solid rgba(17,17,17,0.08);
        border-radius: 16px;
        padding: 1rem 1rem 0.8rem;
        min-height: 120px;
        box-shadow: 0 6px 18px rgba(30,55,87,0.04);
    }
    .metric .label { color: #667382; font-size: 0.72rem; letter-spacing: 0.08em; text-transform: uppercase; }
    .metric .value { font-size: 1.75rem; font-weight: 700; margin-top: 0.6rem; color: #111111; }
    .card { background: #ffffff; border-radius: 18px; border: 1px solid rgba(17,17,17,0.08); padding: 1rem 1rem 1.2rem; box-shadow: 0 8px 20px rgba(17,17,17,0.04); }
    .reminder-item { background: #f8fafc; border: 1px solid rgba(25,92,166,0.12); border-left: 4px solid #3a6ea5; border-radius: 12px; padding: 0.8rem 0.9rem; margin-bottom: 0.3rem; }
    .small-note { font-size: 0.8rem; color: #4d6785; }
    .compact-form { margin-top: 0.2rem; }
    .compact-form .stForm { margin-top: 0; }
    [data-testid="stSidebar"] { background: #edf2f6; }
    .stButton > button {
        background: #111111 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 14px;
        padding: 0.7rem 1.1rem;
        font-weight: 600;
        font-family: 'IBM Plex Mono', monospace;
        width: 100%;
        box-shadow: none !important;
    }
    .stButton > button:hover {
        background: #111111 !important;
        color: #ffffff !important;
        opacity: 1 !important;
    }
    .stButton > button:focus,
    .stButton > button:active {
        background: #111111 !important;
        color: #ffffff !important;
        box-shadow: none !important;
    }
    .stTextInput input, .stSelectbox div, .stDateInput input { background: #ffffff; color: #111111; border: 1px solid rgba(17,17,17,0.12); border-radius: 10px; }
    .stDateInput label, .stTextInput label, .stSelectbox label { font-size: 0.8rem; color: #4f6172; }
    h1, h2, h3, h4, h5, h6 { color: #111111; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class='hero'>
        <h1>FriendVault</h1>
        <p>Local bill tracking for the daily chaos: rent, utilities, subscriptions, groceries, and the little receipts that always seem to arrive at the worst time.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("## FriendVault")
    st.write("A private, offline-first home finance companion for someone who wants fewer missed payments and less mental load.")
    st.markdown("---")
    st.write("Why this matters")
    st.write("Electricity, rent, internet, and subscriptions are easy to forget when they arrive as screenshots, receipts, or paper slips.")
    st.markdown("---")
    st.write("How it helps")
    st.write("- scans bill photos locally")
    st.write("- extracts merchant, date, and amount")
    st.write("- generates reminders automatically")
    st.write("- keeps the data on this computer")

uploaded_files = st.file_uploader("Upload bill or receipt photos", type=["png", "jpg", "jpeg", "tif", "tiff"], accept_multiple_files=True)

bills = db_utils.list_bills(DB_PATH)
reminders = db_utils.list_reminders(DB_PATH)
shopping_items = db_utils.list_shopping_items(DB_PATH)
monthly_summary = db_utils.get_monthly_summary(DB_PATH)

if bills and not reminders:
    for bill in bills:
        db_utils.ensure_reminder_for_bill(DB_PATH, bill)
    reminders = db_utils.list_reminders(DB_PATH)

try:
    total_spend = sum(float((b.get('amount') or '0').replace('$', '').replace(',', '')) for b in bills if str(b.get('amount') or '').replace('$','').replace(',','').replace('.','',1).isdigit())
except Exception:
    total_spend = 0

active_reminders = [r for r in reminders if r.get('status') in ('active', 'scheduled')]
active_due = 0.0
bill_map = {str(b.get('id')): b for b in bills}
for rem in active_reminders:
    bill_id = str(rem.get('bill_id'))
    if bill_id in bill_map:
        amount_text = str(bill_map[bill_id].get('amount') or '0').replace('$', '').replace(',', '')
        try:
            active_due += float(amount_text)
        except Exception:
            pass

metric_cols = st.columns(4)
metric_cols[0].markdown(f"<div class='metric'><div class='label'>Bills saved</div><div class='value'>{len(bills)}</div></div>", unsafe_allow_html=True)
metric_cols[1].markdown(f"<div class='metric'><div class='label'>Total spending</div><div class='value'>${total_spend:.2f}</div></div>", unsafe_allow_html=True)
metric_cols[2].markdown(f"<div class='metric'><div class='label'>Total due</div><div class='value'>${active_due:.2f}</div></div>", unsafe_allow_html=True)
metric_cols[3].markdown("<div class='metric'><div class='label'>Private mode</div><div class='value'>Local</div></div>", unsafe_allow_html=True)

st.markdown("---")
summary_cols = st.columns(min(4, max(1, len(monthly_summary) or 1)))
if monthly_summary:
    for i, row in enumerate(monthly_summary):
        with summary_cols[i]:
            st.markdown(f"<div class='card'><div class='small-note'>{row['month']}</div><div style='font-size: 1.5rem; font-weight:700; margin-top: 0.5rem;'>${row['total']:.2f}</div><div class='small-note' style='margin-top: 0.4rem;'>{row['count']} bills</div></div>", unsafe_allow_html=True)
else:
    with summary_cols[0]:
        st.markdown("<div class='card'><div class='small-note'>Monthly summary</div><div style='font-size: 1.3rem; font-weight:700; margin-top: 0.4rem;'>No bills yet</div></div>", unsafe_allow_html=True)

left_col, right_col = st.columns([1.5, 1])

with right_col:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Add a bill")
    if uploaded_files:
        for uploaded in uploaded_files:
            st.markdown("---")
            img = Image.open(io.BytesIO(uploaded.getvalue()))
            img_disp = ImageOps.contain(img, (700, 700))
            st.image(img_disp, use_column_width=True)

            with st.expander("OCR + extraction"):
                raw_text = ocr_utils.ocr_image(img)
                st.text_area("OCR text", value=raw_text, height=180, key=f"raw_{uploaded.name}")

                suggested_vendor = ocr_utils.suggest_vendor(raw_text)
                suggested_date = ocr_utils.suggest_date(raw_text)
                suggested_amount = ocr_utils.suggest_amount(raw_text)
                parsed_items = ocr_utils.parse_line_items(raw_text)

                vendor = st.text_input("Vendor", value=suggested_vendor or "", key=f"vendor_{uploaded.name}")
                date_str = st.text_input("Date", value=suggested_date or "", key=f"date_{uploaded.name}")
                amount = st.text_input("Amount", value=suggested_amount or "", key=f"amount_{uploaded.name}")
                category = st.selectbox("Category", ["Uncategorized", "Utilities", "Groceries", "Rent", "Transport", "Subscriptions", "Other"], key=f"cat_{uploaded.name}")

                st.markdown("**Detected items**")
                edited_items = []
                if parsed_items:
                    for i, item in enumerate(parsed_items[:10]):
                        cols = st.columns([3, 1])
                        name = cols[0].text_input(f"item_name_{uploaded.name}_{i}", value=item.get("name", ""), key=f"name_{uploaded.name}_{i}")
                        price = cols[1].text_input(f"item_price_{uploaded.name}_{i}", value=item.get("price", ""), key=f"price_{uploaded.name}_{i}")
                        edited_items.append({"name": name, "price": price})
                else:
                    st.write("No line items detected.")

                if st.checkbox("Manual item", key=f"manual_{uploaded.name}"):
                    add_name = st.text_input(f"Manual item name {uploaded.name}", key=f"manual_name_{uploaded.name}")
                    add_price = st.text_input(f"Manual item price {uploaded.name}", key=f"manual_price_{uploaded.name}")
                    if add_name:
                        edited_items.append({"name": add_name, "price": add_price})

                if st.button("Save to FriendVault", key=f"save_{uploaded.name}"):
                    saved_id = db_utils.save_bill(DB_PATH, uploaded, vendor, date_str, amount, category, raw_text, line_items=edited_items)
                    if saved_id:
                        st.success(f"Saved: {vendor}")
                        bill_snapshot = {"id": saved_id, "vendor": vendor, "date": date_str, "amount": amount, "category": category}
                        db_utils.ensure_reminder_for_bill(DB_PATH, bill_snapshot)
                        if edited_items:
                            db_utils.sync_shopping_items_from_bill(DB_PATH, edited_items, vendor)
                        trigger_local_notification("FriendVault", f"Saved bill for {vendor}.")
                        st.rerun()
                    else:
                        st.error("Failed to save record")
    else:
        st.info("No file uploaded yet. Add a bill picture to begin.")
    st.markdown("</div>", unsafe_allow_html=True)

with left_col:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Upcoming reminders")
    reminder_rows = db_utils.list_reminders(DB_PATH)
    if reminder_rows:
        for rem in reminder_rows:
            if rem.get("status") in ("paid", "cancelled"):
                continue
            title = rem.get("title") or "Bill reminder"
            due = rem.get("due_date") or "Soon"
            category = rem.get("category") or "General"
            description = rem.get("description") or ""
            reminder_id = rem.get("id")

            st.markdown(f"<div class='reminder-item'><div class='small-note'>{category}</div><div style='font-size: 1.06rem; font-weight: 700; margin-top: 0.25rem;'>{title}</div><div style='margin-top: 0.35rem; color: #495664;'>Due: {due}</div><div style='margin-top: 0.25rem; color: #495664;'>{description}</div></div>", unsafe_allow_html=True)
            with st.form(key=f"reminder_form_{reminder_id}"):
                st.markdown("<div style='font-size: 0.78rem; color: #4d6785; margin-bottom: 0.25rem;'>Update reminder</div>", unsafe_allow_html=True)
                try:
                    parsed_due = datetime.strptime(due, "%Y-%m-%d").date() if due and len(due) >= 8 else datetime.today().date()
                    if parsed_due.year < 2000:
                        parsed_due = datetime.today().date()
                except Exception:
                    parsed_due = datetime.today().date()
                new_due = st.date_input(
                    "Due date",
                    value=parsed_due,
                    min_value=datetime(2020, 1, 1).date(),
                    max_value=datetime(2035, 12, 31).date(),
                    key=f"due_{reminder_id}",
                )
                btn_cols = st.columns(3)
                if btn_cols[0].form_submit_button("Set reminder"):
                    db_utils.update_reminder_due_date(DB_PATH, reminder_id, new_due.isoformat())
                    db_utils.set_reminder_status(DB_PATH, reminder_id, "active")
                    st.success(f"Reminder set for {title}")
                    trigger_local_notification("FriendVault", f"Reminder set: {title}")
                    st.rerun()
                if btn_cols[1].form_submit_button("Cancel reminder"):
                    db_utils.set_reminder_status(DB_PATH, reminder_id, "cancelled")
                    st.info(f"Cancelled reminder: {title}")
                    st.rerun()
                if btn_cols[2].form_submit_button("Mark paid"):
                    db_utils.mark_reminder_paid(DB_PATH, reminder_id)
                    st.success(f"Marked as paid: {title}")
                    trigger_local_notification("FriendVault", f"Marked paid: {title}")
                    st.rerun()
    else:
        st.info("No reminders yet — save a bill to generate one.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='card' style='margin-top: 1rem;'>", unsafe_allow_html=True)
    st.subheader("Shopping list")
    shopping_rows = db_utils.list_shopping_items(DB_PATH)
    if shopping_rows:
        for row in shopping_rows:
            checked = st.checkbox(row['name'], value=bool(row['bought']), key=f"shop_{row['id']}")
            if checked != bool(row['bought']):
                db_utils.toggle_shopping_item(DB_PATH, row['id'], checked)
                st.rerun()
    else:
        st.info("No grocery items detected yet — add a grocery receipt to generate items.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='card' style='margin-top: 1rem;'>", unsafe_allow_html=True)
    st.subheader("Saved bills")
    row_data = db_utils.list_bills(DB_PATH)
    if row_data:
        for bill in row_data[:8]:
            vendor = bill.get("vendor") or "Unknown"
            date = bill.get("date") or "-"
            amount = bill.get("amount") or "-"
            category = bill.get("category") or "General"
            bill_id = bill.get("id")
            st.markdown(
                f"""
                <div class='reminder-item'>
                    <div style='display: flex; justify-content: space-between; gap: 1rem;'>
                        <div>
                            <div style='font-weight: 700;'>{vendor}</div>
                            <div class='small-note' style='margin-top:0.25rem;'>{category} • {date}</div>
                        </div>
                        <div style='font-weight:700; color:#1d3f72;'>${amount}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            with st.form(key=f"delete_bill_{bill_id}"):
                if st.form_submit_button("Delete bill"):
                    db_utils.delete_bill(DB_PATH, bill_id)
                    st.warning(f"Deleted saved bill: {vendor}")
                    st.rerun()
    else:
        st.info("No saved bills yet.")
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='margin-top: 1.4rem; color: #596d7f; text-align: center;'>FriendVault • offline-first • local-only privacy</div>", unsafe_allow_html=True)
