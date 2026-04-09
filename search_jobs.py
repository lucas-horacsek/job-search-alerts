#!/usr/bin/env python3
"""
Automated Job Search Alerts
Searches for consulting and quant internship roles, then emails a summary.
Designed to run weekly via GitHub Actions.
"""

import os
import json
import smtplib
import hashlib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from duckduckgo_search import DDGS

# ─── Configuration ────────────────────────────────────────────────────────────

RECIPIENT_EMAIL = os.environ.get("RECIPIENT_EMAIL", "lucassh6@gmail.com")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "lucassh6@gmail.com")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")

# How many results to fetch per query
MAX_RESULTS_PER_QUERY = 8

# File to track previously seen results (persisted via GitHub Actions cache)
SEEN_FILE = "seen_listings.json"

# ─── Search Queries ───────────────────────────────────────────────────────────

CONSULTING_QUERIES = [
    "consulting internship Ottawa summer 2027",
    "management consulting intern Ottawa 2027",
    "strategy consulting internship Ottawa Canada summer 2027",
    "consulting summer analyst Ottawa 2027",
    "consulting intern Ottawa Canada 2027 apply",
    "Big 4 consulting internship Ottawa 2027",
    "Deloitte McKinsey BCG Accenture internship Ottawa 2027",
]

QUANT_QUERIES = [
    # Canada
    "quantitative analyst internship 2027 Canada",
    "quant trading intern 2027 Toronto Montreal Ottawa",
    "quantitative research internship Canada 2027",
    "quant developer intern Toronto 2027",
    "quantitative finance internship Montreal 2027",
    # United States
    "quant intern 2027 New York Chicago",
    "quantitative trading internship 2027 USA",
    "quantitative analyst intern summer 2027 New York",
    "quant research intern 2027 Boston San Francisco",
    "quant developer internship 2027 USA",
    # Europe
    "quant internship 2027 London",
    "quantitative analyst intern 2027 Europe",
    "quant trading internship London Amsterdam 2027",
    "quantitative research intern 2027 Zurich Paris",
]


def search_ddg(query: str, max_results: int = MAX_RESULTS_PER_QUERY) -> list[dict]:
    """Search DuckDuckGo and return results."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        return results
    except Exception as e:
        print(f"  [WARN] Search failed for '{query}': {e}")
        return []


def deduplicate_results(results: list[dict]) -> list[dict]:
    """Remove duplicate results based on URL."""
    seen_urls = set()
    unique = []
    for r in results:
        url = r.get("href", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique.append(r)
    return unique


def load_seen() -> set:
    """Load previously seen listing hashes."""
    if os.path.exists(SEEN_FILE):
        try:
            with open(SEEN_FILE, "r") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()


def save_seen(seen: set):
    """Save seen listing hashes."""
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)


def result_hash(result: dict) -> str:
    """Create a hash for a result to detect duplicates across runs."""
    key = result.get("href", "") + result.get("title", "")
    return hashlib.md5(key.encode()).hexdigest()


def filter_new(results: list[dict], seen: set) -> tuple[list[dict], set]:
    """Filter out previously seen results and update the seen set."""
    new_results = []
    for r in results:
        h = result_hash(r)
        if h not in seen:
            new_results.append(r)
            seen.add(h)
    return new_results, seen


def run_search(queries: list[str], category: str) -> list[dict]:
    """Run all queries for a category and return deduplicated results."""
    all_results = []
    for q in queries:
        print(f"  Searching: {q}")
        results = search_ddg(q)
        all_results.extend(results)
    unique = deduplicate_results(all_results)
    print(f"  [{category}] Found {len(unique)} unique results from {len(queries)} queries.")
    return unique


def format_results_html(results: list[dict], category: str, new_only: list[dict]) -> str:
    """Format results into an HTML section."""
    if not results:
        return f"""
        <div style="margin-bottom: 30px;">
            <h2 style="color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: 8px;">{category}</h2>
            <p style="color: #666;">No results found this week. The search will continue next week.</p>
        </div>
        """

    # Separate new and previously seen
    new_hashes = {result_hash(r) for r in new_only}

    html = f"""
    <div style="margin-bottom: 30px;">
        <h2 style="color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: 8px;">
            {category}
            <span style="font-size: 14px; color: #666; font-weight: normal;">
                ({len(new_only)} new, {len(results)} total)
            </span>
        </h2>
    """

    for r in results:
        title = r.get("title", "No Title")
        url = r.get("href", "#")
        body = r.get("body", "No description available.")
        is_new = result_hash(r) in new_hashes
        new_badge = '<span style="background: #34a853; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px; margin-left: 8px;">NEW</span>' if is_new else ""

        html += f"""
        <div style="margin: 12px 0; padding: 14px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid {'#34a853' if is_new else '#dadce0'};">
            <a href="{url}" style="color: #1a73e8; text-decoration: none; font-weight: 600; font-size: 15px;">
                {title}
            </a>
            {new_badge}
            <p style="color: #555; margin: 6px 0 0 0; font-size: 13px; line-height: 1.5;">
                {body}
            </p>
            <p style="margin: 4px 0 0 0;">
                <a href="{url}" style="color: #888; font-size: 11px; text-decoration: none;">{url[:80]}...</a>
            </p>
        </div>
        """

    html += "</div>"
    return html


def build_email(consulting_results, consulting_new, quant_results, quant_new) -> str:
    """Build the full HTML email."""
    date_str = datetime.now().strftime("%B %d, %Y")

    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 700px; margin: 0 auto; padding: 20px; color: #333;">
        <div style="text-align: center; padding: 20px 0; border-bottom: 1px solid #e0e0e0; margin-bottom: 25px;">
            <h1 style="color: #202124; margin: 0; font-size: 24px;">Weekly Job Search Report</h1>
            <p style="color: #666; margin: 8px 0 0 0; font-size: 14px;">{date_str}</p>
        </div>

        <div style="background: #e8f0fe; padding: 14px 18px; border-radius: 8px; margin-bottom: 25px; font-size: 14px; color: #1a73e8;">
            <strong>Summary:</strong> {len(consulting_new)} new consulting listing(s) &bull; {len(quant_new)} new quant listing(s)
        </div>

        {format_results_html(consulting_results, "Consulting Internships — Ottawa (Summer 2027)", consulting_new)}
        {format_results_html(quant_results, "Quant Internships — Canada / US / Europe (Any Term)", quant_new)}

        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0; text-align: center; color: #999; font-size: 12px;">
            <p>Automated by GitHub Actions &bull; Searches powered by DuckDuckGo</p>
            <p>To stop these emails, disable the workflow in your GitHub repository.</p>
        </div>
    </body>
    </html>
    """
    return html


def send_email(subject: str, html_body: str, plain_body: str):
    """Send email via Gmail SMTP."""
    if not GMAIL_APP_PASSWORD:
        print("[ERROR] GMAIL_APP_PASSWORD not set. Skipping email send.")
        print("--- EMAIL PREVIEW (Subject) ---")
        print(subject)
        print("--- EMAIL PREVIEW (Plain Text) ---")
        print(plain_body[:2000])
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECIPIENT_EMAIL

    msg.attach(MIMEText(plain_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, GMAIL_APP_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, msg.as_string())
        print("[OK] Email sent successfully!")
    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")
        raise


def main():
    print("=" * 60)
    print(f"Job Search Alert — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    # Load previously seen listings
    seen = load_seen()
    initial_seen_count = len(seen)
    print(f"Loaded {initial_seen_count} previously seen listings.\n")

    # --- Consulting Search ---
    print("[1/2] Searching for CONSULTING internships in Ottawa...")
    consulting_all = run_search(CONSULTING_QUERIES, "Consulting")
    consulting_new, seen = filter_new(consulting_all, seen)
    print(f"  → {len(consulting_new)} new results\n")

    # --- Quant Search ---
    print("[2/2] Searching for QUANT internships (Canada/US/Europe)...")
    quant_all = run_search(QUANT_QUERIES, "Quant")
    quant_new, seen = filter_new(quant_all, seen)
    print(f"  → {len(quant_new)} new results\n")

    # Save updated seen file
    save_seen(seen)
    print(f"Updated seen listings: {initial_seen_count} → {len(seen)}\n")

    # --- Build & Send Email ---
    total_new = len(consulting_new) + len(quant_new)
    date_str = datetime.now().strftime("%b %d, %Y")
    subject = f"Weekly Job Alerts — {total_new} new listing(s) — {date_str}"

    html_body = build_email(consulting_all, consulting_new, quant_all, quant_new)

    # Plain text fallback
    plain_lines = [f"Weekly Job Search Report — {date_str}", ""]
    plain_lines.append(f"CONSULTING INTERNSHIPS — OTTAWA (Summer 2027): {len(consulting_new)} new")
    for r in consulting_new:
        plain_lines.append(f"  • {r.get('title', 'N/A')}")
        plain_lines.append(f"    {r.get('href', '')}")
    plain_lines.append("")
    plain_lines.append(f"QUANT INTERNSHIPS — Canada/US/Europe (Any Term): {len(quant_new)} new")
    for r in quant_new:
        plain_lines.append(f"  • {r.get('title', 'N/A')}")
        plain_lines.append(f"    {r.get('href', '')}")

    plain_body = "\n".join(plain_lines)

    send_email(subject, html_body, plain_body)

    print("\nDone!")


if __name__ == "__main__":
    main()
