# Personal Networth Tracker

A small Flask app to track accounts and visualize net worth over time. 

## Quick start (minimal, cross-platform)

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Run the app:

```bash
python app.py
```

3. Open your browser at: http://localhost:5000

Optional: to isolate project dependencies, you may create and activate a virtual environment before installing (recommended for multi-project machines). This step is not required.

## Minimal feature summary

- User management (sign-up, login, change password)
- Add/update/archive/remove assets and liabilities from a user account
- Historical account values and daily net worth charts 
- Multi-currency support (fiat + crypto) with live rates and fallback data
- Multiple themes (including a dark theme)
