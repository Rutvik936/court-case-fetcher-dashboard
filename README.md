# 🏛️ Court Case Fetcher & Dashboard

A full-stack web app built to scrape real-time court case metadata from the [Pune District Court eCourts portal](https://pune.dcourts.gov.in/), display results, store logs, and generate downloadable PDFs for legal case references.

---

## 🎯 Project Motive

Court data in India is available online but difficult to access programmatically due to dynamic pages, CAPTCHAs, and inconsistent formats.  
This project solves that by:

- Automating data extraction from the eCourts portal
- Providing a clean UI for users to search court cases
- Logging each query with detailed status
- Offering PDF generation for documentation/sharing

---

## ⚙️ What the Project Does

✅ Takes user input:
- Court Complex
- Case Type
- Case Number
- Filing Year

✅ Then it:
- Launches **Playwright** browser
- Loads [pune.dcourts.gov.in](https://pune.dcourts.gov.in/)
- Waits for manual CAPTCHA input
- Submits the form & scrapes:
  - Petitioner & Respondent
  - CNR Number
  - Filing Date
  - Next Hearing Date
  - Business and Purpose
- Saves search & result in **SQLite DB**
- Renders clean results in browser
- Allows downloading case PDF

✅ History:
- `/logs` route shows searchable query history with status + PDF links

---

## 🧠 Tech Stack

| Layer       | Tool / Tech                   |
|-------------|-------------------------------|
| Frontend    | HTML, CSS (Custom), Jinja2    |
| Backend     | Python, Flask                 |
| Scraping    | Playwright (async), BeautifulSoup |
| Database    | SQLite                        |
| PDF         | FPDF                          |
| UI/UX       | Poppins Font, Fully Responsive |

---

## 🛠️ Folder Structure

```
court-case-fetcher-dashboard/
├── app.py                 # Flask app (routes, PDF generation, DB insert)
├── scraper.py             # Playwright + BS4 scraper
├── templates/
│   ├── index.html         # Input + Results Page
│   └── logs.html          # Search History + PDF download
├── db/
│   └── search_logs.db     # SQLite database file
├── requirements.txt       # Python dependencies
├── .gitignore             # Ignore pycache, *.db, etc.
├── LICENSE                # MIT License
└── README.md              # You're here!
```

---

## 🔐 CAPTCHA Handling Strategy

- CAPTCHA solving is **manual**  
- User solves the CAPTCHA in browser window
- Scraper waits until the form is submitted, then continues

> ⚠️ Automatic solving is not used for ethical and legal reasons.

---

## 🎥 Demo Video

👉 [Watch Demo](https://your-demo-link.com)


---
