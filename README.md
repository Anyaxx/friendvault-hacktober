# FriendVault — local bill & receipt assistant

FriendVault is a privacy-first, local-only tool for tracking household bills, recurring reminders, and grocery receipts. It is designed for the Hacktoberfest Weekend Challenge: Build for a Friend.

The app lets a user upload a receipt or bill photo, run OCR locally, extract key details, generate reminders, and review a monthly summary — all without sending personal financial data to a remote service.

## Features

- Upload bill or receipt photos locally
- OCR extraction for vendor, date, and amount
- Grocery item extraction from receipts
- Reminder generation for recurring categories like utilities, rent, and subscriptions
- Monthly spending summary cards
- Saved bill deletion
- Shopping list tracking
- Local-only storage in SQLite

## Why this exists

This project was built for a real person who needed a simpler way to track what was due, what had been paid, and what was still piling up in paper receipts and screenshots.

## Quick start

1. Install Tesseract on your machine:
   - macOS: `brew install tesseract`
   - Ubuntu/Debian: `sudo apt install tesseract-ocr`

2. Create a Python virtual environment and install dependencies:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. Run the app:

   ```bash
   streamlit run app/main.py
   ```

## Project structure

- `app/main.py` — Streamlit UI and dashboard
- `app/db.py` — SQLite storage and reminder logic
- `app/ocr.py` — local OCR and receipt parsing
- `requirements.txt` — app dependencies

## Notes

Everything is stored on the device in the local data folder. No data is sent to external services by default.
