from flask import Flask, render_template, request, send_file
import os
import sqlite3
import datetime
import asyncio
from scraper import run_scraper
from fpdf import FPDF
import json

app = Flask(__name__)
DB_PATH = "db/cases.db"

# Initialize database with proper structure
def init_db():
    os.makedirs("db", exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        # Drop old table if exists to ensure clean start
        conn.execute("DROP TABLE IF EXISTS searches")
        # Create new table with all required fields
        conn.execute('''
            CREATE TABLE searches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                court_complex TEXT NOT NULL,
                case_type TEXT NOT NULL,
                case_number TEXT NOT NULL,
                year TEXT NOT NULL,
                status TEXT NOT NULL,
                result TEXT,
                error_message TEXT
            )
        ''')

init_db()

def get_logs():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row  # Allows dictionary-style access
        logs = conn.execute('SELECT * FROM searches ORDER BY timestamp DESC').fetchall()
        
        formatted_logs = []
        for log in logs:
            # Safely handle result JSON parsing
            result_data = {}
            if log['result']:
                try:
                    result_data = json.loads(log['result'])
                except json.JSONDecodeError:
                    result_data = {}
            
            # Build the log entry with all required fields
            formatted_logs.append({
                'timestamp': log['timestamp'],
                'court_complex': log['court_complex'],
                'case_type': log['case_type'],
                'case_number': log['case_number'],
                'year': log['year'],
                'status': log['status'],  # Now guaranteed to exist
                'result': {
                    'cnr_number': result_data.get('cnr_number'),
                    'petitioner': result_data.get('petitioner'),
                    'respondent': result_data.get('respondent'),
                    'next_hearing_date': result_data.get('next_hearing_date'),
                    'court_name': result_data.get('court_name'),
                    'case_title': result_data.get('case_title'),
                    'business': result_data.get('business'),
                    'next_purpose': result_data.get('next_purpose'),
                    'error_message': log['error_message']
                }
            })
        return formatted_logs

def generate_pdf(cnr_number, case_data):
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "District and Session Court, Pune", 0, 1, 'C')
    
    # Case details
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f"In The Court Of: {case_data.get('court_name', 'N/A')}", 0, 1)
    pdf.cell(0, 10, f"CNR Number: {case_data.get('cnr_number', cnr_number)}", 0, 1)
    pdf.cell(0, 10, f"Case Number: {case_data.get('case_number', 'N/A')}", 0, 1)
    pdf.cell(0, 10, f"Date: {case_data.get('hearing_date', 'N/A')}", 0, 1)
    
    # Case title
    pdf.set_font("Arial", 'I', 12)
    pdf.multi_cell(0, 10, case_data.get('case_title', 'N/A'))
    
    # Business table
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "Daily Status", 0, 1)
    
    # Table headers
    pdf.set_font("Arial", 'B', 12)
    col_widths = [60, 60, 60]
    headers = ["Business", "Next Purpose", "Next Hearing Date"]
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 10, header, border=1, align='C')
    pdf.ln()
    
    # Table content
    pdf.set_font("Arial", '', 12)
    pdf.cell(col_widths[0], 10, case_data.get('business', 'N/A'), border=1)
    pdf.cell(col_widths[1], 10, case_data.get('next_purpose', 'N/A'), border=1)
    pdf.cell(col_widths[2], 10, case_data.get('next_hearing_date', 'N/A'), border=1)
    
    # Save to temp file
    pdf_path = f"case_{cnr_number}.pdf"
    pdf.output(pdf_path)
    return pdf_path

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        court_complex = request.form["court_complex"]
        case_type = request.form["case_type"]
        case_number = request.form["case_number"]
        year = request.form["year"]

        try:
            result = asyncio.run(run_scraper(court_complex, case_type, case_number, year))
            
            # Determine status and prepare data
            status = 'success' if result and 'petitioner' in result else 'error'
            error_msg = result.get('error', 'Unknown error') if status == 'error' else None
            
            result_data = {
                'petitioner': result.get('petitioner'),
                'respondent': result.get('respondent'),
                'next_hearing_date': result.get('next_hearing_date'),
                'court_name': result.get('court_name'),
                'case_title': result.get('case_title'),
                'cnr_number': result.get('cnr_number'),
                'business': result.get('business'),
                'next_purpose': result.get('next_purpose')
            } if status == 'success' else None

            with sqlite3.connect(DB_PATH) as conn:
                conn.execute('''
                    INSERT INTO searches (
                        timestamp, court_complex, case_type, case_number, year,
                        status, result, error_message
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    court_complex,
                    case_type,
                    case_number,
                    year,
                    status,
                    json.dumps(result_data) if status == 'success' else None,
                    error_msg
                ))

            return render_template("index.html", result=result if status == 'success' else None)

        except Exception as e:
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute('''
                    INSERT INTO searches (
                        timestamp, court_complex, case_type, case_number, year,
                        status, result, error_message
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    court_complex,
                    case_type,
                    case_number,
                    year,
                    'error',
                    None,
                    str(e)
                ))
            
            return render_template("index.html", result=None)
    
    return render_template("index.html")

@app.route('/logs')
def show_logs():
    try:
        logs = get_logs()
        return render_template('logs.html', logs=logs)
    except Exception as e:
        app.logger.error(f"Error loading logs: {str(e)}")
        return render_template('logs.html', logs=[])

@app.route('/generate_pdf/<cnr_number>')
def download_pdf(cnr_number):
    try:
        case_data = {
            "court_name": request.args.get("court_name", "N/A"),
            "cnr_number": cnr_number,
            "case_number": request.args.get("case_number", "N/A"),
            "hearing_date": request.args.get("hearing_date", "N/A"),
            "case_title": request.args.get("case_title", "N/A"),
            "business": request.args.get("business", "N/A"),
            "next_purpose": request.args.get("next_purpose", "N/A"),
            "next_hearing_date": request.args.get("next_hearing_date", "N/A")
        }

        pdf_path = generate_pdf(cnr_number, case_data)
        return send_file(pdf_path, as_attachment=True)
    except Exception as e:
        return f"Error generating PDF: {str(e)}", 500
    finally:
        if 'pdf_path' in locals() and os.path.exists(pdf_path):
            os.unlink(pdf_path)

if __name__ == "__main__":
    app.run(debug=True)