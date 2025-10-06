import os
import csv
import re
import argparse
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

DEMO_FILE_DEFAULT = "demo.html"
LOGIN_URL_DEFAULT = "https://my.koelnmesse.io/en/login"
OUTPUT_CSV_DEFAULT = "exhibitors_with_contact.csv"

def parse_demo_links(demo_file):
    with open(demo_file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
    exhibitors = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        text = a.get_text(strip=True)
        # filter for exhibitor links (adjust if your links differ)
        if "/exhibitor/" in href.lower() or "anuga.com/exhibitor" in href.lower():
            exhibitors.append((text, href))
    # dedupe while keeping order
    seen = set()
    out = []
    for n,u in exhibitors:
        if u in seen: continue
        seen.add(u)
        out.append((n,u))
    return out

_phone_regex = re.compile(r'(\+?\d[\d\-\s().]{6,}\d)')

def extract_phone_email(html):
    soup = BeautifulSoup(html, "html.parser")
    # phone
    phone = None
    tel = soup.select_one("a[href^='tel:']")
    if tel:
        phone = tel.get("href").split(":",1)[1].strip()
    else:
        text = soup.get_text(" ")
        m = _phone_regex.search(text)
        if m:
            phone = m.group(1).strip()
    # email
    email = None
    mail = soup.select_one("a[href^='mailto:']")
    if mail:
        email = mail.get("href").split(":",1)[1].strip()
    else:
        m = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', soup.get_text(" "))
        if m:
            email = m.group(0)
    return (phone or "N/A", email or "N/A")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", default=DEMO_FILE_DEFAULT, help="Local exhibitor list HTML (demo.html)")
    ap.add_argument("--login-url", default=LOGIN_URL_DEFAULT, help="Login URL (Koelnmesse SSO)")
    ap.add_argument("--out", default=OUTPUT_CSV_DEFAULT, help="Output CSV filename")
    ap.add_argument("--manual", action="store_true",
                    help="Open browser and wait for you to log in manually (useful for CAPTCHA/MFA).")
    ap.add_argument("--headless", action="store_true", help="Run browser headless (may fail for interactive login).")
    args = ap.parse_args()

    if not os.path.exists(args.demo):
        print("ERROR: demo file not found:", args.demo)
        return

    exhibitors = parse_demo_links(args.demo)
    if not exhibitors:
        print("No exhibitor links found in", args.demo)
        return
    print(f"Found {len(exhibitors)} exhibitor links in {args.demo} (will visit them in the browser)")

    email = os.getenv("KOELNMESSE_EMAIL")
    password = os.getenv("KOELNMESSE_PASS")
    if not args.manual and (not email or not password):
        print("No credentials found in KOELNMESSE_EMAIL / KOELNMESSE_PASS environment variables.")
        # prompt securely (local only)
        email = input("Koelnmesse email: ").strip()
        password = input("Password: ").strip()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=args.headless)
        context = browser.new_context()
        page = context.new_page()
        print("Opening login page:", args.login_url)
        page.goto(args.login_url, wait_until="domcontentloaded")
        # wait for login form (the page you uploaded uses id=loginEmail / id=loginPassword)
        try:
            page.wait_for_selector("#loginEmail", timeout=10000)
            print("Login form appears to be present (selector '#loginEmail').")
        except Exception:
            print("Warning: login form not found quickly — the site may have changed. Proceeding anyway.")

        if args.manual:
            print("\nManual login mode: the browser is open. Please log in manually.\nAfter successful login press Enter here to continue.")
            input("Press Enter after you have logged in...")
        else:
            # auto-fill and submit
            try:
                print("Filling credentials and submitting form (automated).")
                page.fill("#loginEmail", email)
                page.fill("#loginPassword", password)
                # try common submit selectors
                try:
                    page.click("button[type=submit]")
                except Exception:
                    page.click("button:has-text('Login now')")
                # wait for the login form to disappear or a navigation
                try:
                    page.wait_for_selector("#loginEmail", state="detached", timeout=10000)
                    print("Login form disappeared — likely logged in.")
                except Exception:
                    print("Login form still present after submit — login may have failed or 2FA/CAPTCHA is required.")
                    print("You can re-run with --manual to login by hand.")
                    # continue anyway
            except Exception as e:
                print("Automated login attempt failed:", e)
                print("Try running with --manual to log in interactively.")
                browser.close()
                return

        # now we should have the cookies in the browser context; visit each exhibitor page
        rows = []
        for name, url in exhibitors:
            print("Visiting:", name, url)
            try:
                page.goto(url, wait_until="networkidle", timeout=30000)
                html = page.content()
                phone, email_addr = extract_phone_email(html)
            except Exception as e:
                print("  ERROR visiting page:", e)
                phone, email_addr = "N/A", "N/A"
            print(f"  -> phone: {phone}  email: {email_addr}")
            rows.append([name, url, phone, email_addr])

        # write CSV
        with open(args.out, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Name", "Link", "Phone", "Email"])
            writer.writerows(rows)
        print("Saved results to", args.out)
        browser.close()

if __name__ == "__main__":
    main()
