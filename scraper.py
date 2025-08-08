import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import json

# ORIGINAL FUNCTIONS (UNCHANGED)
def extract_petitioner(soup):
    try:
        return soup.select_one("div.Petitioner ul li p").text.strip()
    except:
        return "N/A"

def extract_respondents(soup):
    try:
        items = soup.select("div.respondent ul li p")
        return ", ".join([item.get_text(strip=True) for item in items])
    except:
        return "N/A"

def extract_case_details(soup):
    try:
        table = soup.find("caption", string="Case Details").find_parent("table")
        cells = table.find("tbody").find("tr").find_all("td")
        return {
            "filing_date": cells[2].get_text(strip=True),
            "cnr_number": cells[5].get_text(strip=True)
        }
    except:
        return {
            "filing_date": "N/A",
            "cnr_number": "N/A"
        }

# UPDATED FUNCTION (now returns dict)
def extract_case_status(soup):
    try:
        table = soup.find("caption", string="Case Status").find_parent("table")
        cells = table.find("tbody").find("tr").find_all("td")
        return {
            "next_hearing_date": cells[1].get_text(strip=True) if cells[1].get_text(strip=True) else cells[0].get_text(strip=True),
            "next_purpose": cells[2].get_text(strip=True)  # Verify cell index matches actual page
        }
    except:
        return {
            "next_hearing_date": "N/A",
            "next_purpose": "N/A"
        }

# NEW HELPER FUNCTIONS FOR PDF
def extract_case_title(petitioner, respondent):
    """Combine petitioner and respondent for case title"""
    return f"{petitioner} Versus {respondent}"

def extract_business_details(html):
    """Extract business text from business page HTML"""
    try:
        soup = BeautifulSoup(html, "html.parser")
        business_cell = soup.find("td", {"data-th": "Business"})  # This line was missing
        if business_cell:
            return business_cell.get_text(strip=True)
        # Fallback to original selector
        return soup.find("div", class_="business-details").get_text(strip=True)
    except:
        return "N/A"
# MAIN SCRAPER FUNCTION (UPDATED)
async def run_scraper(court_complex, case_type, case_number, year):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=50)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto("https://pune.dcourts.gov.in/case-status-search-by-case-number/", timeout=60000)
        await page.wait_for_selector("#chkYes", timeout=60000)
        await page.check("#chkYes")

        await page.select_option("#est_code", label=court_complex)
        await page.select_option("#case_type", label=case_type)
        await page.fill("#reg_no", case_number)
        await page.fill("#reg_year", year)

        print("⚠️ Please solve CAPTCHA in browser, then press ENTER.")
        input("➡️ After solving the CAPTCHA and clicking 'Search', press ENTER to continue...")

        await page.wait_for_selector("a.viewCnrDetails", timeout=30000)
        await page.click("a.viewCnrDetails")
        await page.wait_for_timeout(4000)
        await page.wait_for_selector("#cnrResultsDetails", timeout=30000)
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")

        # Data extraction
        details = extract_case_details(soup)
        petitioner = extract_petitioner(soup)
        respondents = extract_respondents(soup)
        status = extract_case_status(soup)  # Now returns dict

        # Initialize defaults
        pdf_link = "Not Available"
        business_text = "N/A"

        try:
            # Business details and PDF handling
            business_links = await page.locator("a#getBusiness").all()
            if business_links:
                await business_links[-1].click()
                await page.wait_for_load_state("networkidle")
                business_html = await page.content()
                business_text = extract_business_details(business_html)

        except Exception as e:
            print("❌ Business/PDF extraction error:", e)

        await browser.close()

        return {
            # Original fields
            "petitioner": petitioner,
            "respondent": respondents,
            "filing_date": details["filing_date"],
            "next_hearing_date": status["next_hearing_date"],
            "cnr_number": details["cnr_number"],
            # New fields for PDF
            "court_name": "DISTRICT JUDGE-8 AND ADDL. SESSIONS JUDGE PUNE",
            "case_title": extract_case_title(petitioner, respondents),
            "business": business_text,
            "next_purpose": status["next_purpose"],
            "case_number": f"{case_type}/{case_number}/{year}"
        }

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 5:
        print("Usage: python scraper.py <CourtComplex> <CaseType> <CaseNumber> <Year>")
    else:
        output = asyncio.run(run_scraper(*sys.argv[1:]))
        print(json.dumps(output, indent=2))