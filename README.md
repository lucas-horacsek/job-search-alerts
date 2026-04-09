# Automated Job Search Alerts

Weekly automated email alerts for internship opportunities, powered by GitHub Actions.

## What It Searches

### 1. Consulting Internships — Ottawa (Summer 2027)
- Management consulting, strategy consulting, Big 4 firms
- Focused on Ottawa, Canada

### 2. Quant Internships — Canada / US / Europe (Any Term)
- Quantitative analyst, quant trading, quant research, quant developer
- Cities: Toronto, Montreal, Ottawa, New York, Chicago, Boston, San Francisco, London, Amsterdam, Zurich, Paris

## How It Works

1. **GitHub Actions** triggers the workflow every Monday at 9:00 AM ET
2. **Python script** searches DuckDuckGo for job listings across multiple queries
3. Results are **deduplicated** and compared against previously seen listings
4. A **formatted HTML email** is sent to your Gmail with new and existing results
5. Seen listings are cached so you only get notified of new postings

## Setup

### 1. Create a Gmail App Password

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Make sure **2-Step Verification** is enabled
3. Go to [App Passwords](https://myaccount.google.com/apppasswords)
4. Select app: **Mail**, device: **Other** (name it "Job Alerts")
5. Copy the 16-character password

### 2. Add GitHub Secrets

Go to your repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Add these three secrets:

| Secret Name | Value |
|---|---|
| `SENDER_EMAIL` | `lucassh6@gmail.com` |
| `RECIPIENT_EMAIL` | `lucassh6@gmail.com` |
| `GMAIL_APP_PASSWORD` | Your 16-character app password |

### 3. Enable the Workflow

The workflow runs automatically every Monday. To test immediately:

1. Go to **Actions** tab in your repo
2. Select **Weekly Job Search Alerts**
3. Click **Run workflow**

## Customization

### Add/Remove Search Queries

Edit the `CONSULTING_QUERIES` and `QUANT_QUERIES` lists in `search_jobs.py` to adjust what gets searched.

### Change Schedule

Edit the cron expression in `.github/workflows/job-search.yml`:

```yaml
schedule:
  - cron: "0 13 * * 1"  # Monday 9am ET (1pm UTC)
```

### Change Email Recipient

Update the `RECIPIENT_EMAIL` secret in your repo settings.

## Cost

**Free!** GitHub Actions provides 2,000 minutes/month for free on private repos (unlimited on public repos). Each run takes ~1-2 minutes.
