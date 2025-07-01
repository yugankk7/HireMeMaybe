# HireMeMaybe

This repository contains a simple automation script that demonstrates how one
might automatically apply to job listings on [Naukri.com](https://www.naukri.com)
using Selenium.

## Setup

1. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```
2. Download the appropriate WebDriver for your browser (e.g. `chromedriver`)
   and ensure it is available on your system `PATH`.
3. Set your OpenAI API key in the `OPENAI_API_KEY` environment variable if you
   want to generate cover letters (the script uses the `gpt-4o-mini` model but
   does not generate letters by default).

## Usage

Edit `apply_naukri.py` and fill in your login credentials and file paths. Then
run the script:

```bash
python apply_naukri.py
```

This is only a basic example. You may need to adapt the element selectors and
workflow to match changes on the website. Always ensure that you comply with
Naukri.com's terms of service when running automated scripts.
If enabled, the script can use the OpenAI API (via the `gpt-4o-mini` model) to
generate a short cover letter for each job based on your resume, location
preferences and salary range, but this step is disabled by default.
Update the `JobPreferences` section in the script to set your preferred job
roles and locations. Applications that match these preferences are logged in
`applied_jobs.csv`. Jobs that do not match (or encounter an error) are stored in
`skipped_jobs.csv`. Both files are created if missing and appended to on each
run.
