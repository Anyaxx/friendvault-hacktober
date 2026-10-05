# FriendVault

<p align="center">
  <img alt="Hacktoberfest 2026" src="https://img.shields.io/badge/Hacktoberfest-2026-orange" />
  <img alt="Python 3" src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white" />
  <img alt="Streamlit" src="https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white" />
  <img alt="Tesseract OCR" src="https://img.shields.io/badge/OCR-Tesseract-5C7CFA" />
  <img alt="Local-first" src="https://img.shields.io/badge/Privacy-Local%20Only-111827" />
</p>

FriendVault is a privacy-first, local-only bill and receipt tracker built for the Hacktoberfest Weekend Challenge: Build for a Friend.

It helps a real person stay on top of rent, utilities, subscriptions, and the endless stream of paper receipts by scanning them locally, extracting key details, generating reminders, and summarizing what is due and what has been spent.

## Why this project exists

This was built for a friend who needed a simpler way to manage bills without turning everything into a cloud-based finance service or an overwhelming spreadsheet. The goal was to reduce stress, avoid missed payments, and keep personal finance data on the user’s own device.

## Features

- Upload bill or receipt photos locally
- OCR extraction for vendor, date, and amount
- Grocery item extraction from receipts
- Reminder generation for recurring expenses
- Monthly spend summaries
- Saved bill deletion
- Shopping list tracking
- Local-only SQLite storage

## Demo

Run the app locally:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app/main.py
```

Then upload a receipt image or bill photo to see the extracted data, generated summary cards, reminders, and shopping list.

## Project structure

- `app/main.py` — Streamlit dashboard and user flows
- `app/db.py` — local database logic and reminder generation
- `app/ocr.py` — OCR preprocessing and receipt parsing
- `requirements.txt` — Python dependencies

## Open-source AI approach

This app is built around open-source local tooling instead of a hosted API:

- Streamlit for the interface
- Tesseract OCR for local text extraction
- OpenCV for image preprocessing
- SQLite for offline storage

This keeps the app working without internet access and keeps a person’s sensitive bill data on their own machine.

## Why open innovation matters

Open innovation matters here because a closed-billing service would require sending private financial data to a remote platform. With open-source tools, the app can run on a laptop, work offline, be customized, and stay under the user’s control.

That makes it more trustworthy, more private, and more useful for a real friend who wants fewer missed bills and less mental load.

## Notes

Everything is stored on the device in the local `data/` folder. No data is sent to external services by default.

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
