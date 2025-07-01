"""Basic script to automate applying to jobs on Naukri.com using Selenium."""

from dataclasses import dataclass
import os
import csv
from datetime import datetime
import openai
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time


def create_driver():
    """Create and return a Selenium WebDriver instance."""
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    # Change to the driver of your choice
    driver = webdriver.Chrome(options=options)
    return driver


@dataclass
class Credentials:
    username: str
    password: str
    resume_path: str


@dataclass
class JobPreferences:
    locations: list[str]
    job_roles: list[str]
    salary_range: str = ""
    log_path: str = "applied_jobs.csv"
    skipped_log_path: str = "skipped_jobs.csv"


def login(driver: webdriver.Chrome, creds: Credentials) -> None:
    """Log into Naukri using the provided credentials."""
    driver.get('https://www.naukri.com/')
    time.sleep(2)

    login_button = driver.find_element(By.LINK_TEXT, 'Login')
    login_button.click()
    time.sleep(2)

    username_input = driver.find_element(By.ID, 'usernameField')
    password_input = driver.find_element(By.ID, 'passwordField')

    username_input.send_keys(creds.username)
    password_input.send_keys(creds.password)
    password_input.send_keys(Keys.RETURN)
    time.sleep(5)


def search_jobs(driver: webdriver.Chrome, query: str) -> None:
    """Perform a job search with the given query."""
    search_box = driver.find_element(By.ID, 'qsb-keyword-sugg')
    search_box.clear()
    search_box.send_keys(query)
    search_box.send_keys(Keys.RETURN)
    time.sleep(3)


def load_resume(path: str) -> str:
    """Return the resume text from the given file path."""
    with open(path, 'r', encoding='utf-8') as fh:
        return fh.read()


def generate_cover_letter(job_title: str, prefs: JobPreferences, resume: str) -> str:
    """Generate a short cover letter using the OpenAI API."""
    openai.api_key = os.getenv('OPENAI_API_KEY')
    prompt = (
        "Write a brief cover letter for a job titled '{title}'. "
        "The applicant prefers jobs in {location} with a salary around {salary}. "
        "Use this resume:\n{resume}\n"
    ).format(title=job_title, location=", ".join(prefs.locations), salary=prefs.salary_range, resume=resume)
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
        )
        return resp.choices[0].message.content.strip()
    except Exception as exc:
        print(f"OpenAI API error: {exc}")
        return ""


def log_application(company: str, title: str, location: str, path: str) -> None:
    """Append a record of the application to a CSV file."""
    exists = os.path.isfile(path)
    with open(path, "a", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        if not exists:
            writer.writerow(["Company", "Job Title", "Location", "Applied On"])
        writer.writerow([company, title, location, datetime.now().isoformat()])


def log_skipped_job(company: str, title: str, location: str, path: str, reason: str) -> None:
    """Append details of a job that was not applied to."""
    exists = os.path.isfile(path)
    with open(path, "a", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        if not exists:
            writer.writerow(["Company", "Job Title", "Location", "Skipped On", "Reason"])
        writer.writerow([company, title, location, datetime.now().isoformat(), reason])


def apply_to_listings(driver: webdriver.Chrome, prefs: JobPreferences) -> None:
    """Iterate through job listings and apply to those matching preferences."""
    jobs = driver.find_elements(By.CSS_SELECTOR, "article.jobTuple")
    for job in jobs:
        try:
            title_el = job.find_element(By.CSS_SELECTOR, "a.title")
            job_title = title_el.text

            company_el = job.find_element(By.CSS_SELECTOR, "a.compName")
            company_name = company_el.text

            location_text = ""
            try:
                loc_el = job.find_element(By.CSS_SELECTOR, "li.location")
                location_text = loc_el.text
            except Exception:
                pass

            role_match = any(r.lower() in job_title.lower() for r in prefs.job_roles)
            location_match = any(l.lower() in location_text.lower() for l in prefs.locations)

            if role_match and location_match:
                apply_btn = job.find_element(By.CSS_SELECTOR, "button.btn-apply")
                apply_btn.click()
                log_application(company_name, job_title, location_text, prefs.log_path)
                time.sleep(2)
                driver.back()
            else:
                print(f"Skipping {job_title} due to preference mismatch")
                log_skipped_job(
                    company_name,
                    job_title,
                    location_text,
                    prefs.skipped_log_path,
                    "preference mismatch",
                )
        except Exception as exc:
            print(f"Skipping listing due to error: {exc}")
            title = locals().get("job_title", "Unknown")
            company = locals().get("company_name", "Unknown")
            location = locals().get("location_text", "")
            log_skipped_job(
                company,
                title,
                location,
                prefs.skipped_log_path,
                f"error: {exc}",
            )


def main() -> None:
    creds = Credentials(
        username='your_username',
        password='your_password',
        resume_path='/path/to/resume.pdf'
    )
    prefs = JobPreferences(
        locations=['Bangalore', 'Remote'],
        job_roles=['Software Engineer'],
        salary_range='10-12 LPA'
    )

    driver = create_driver()
    try:
        login(driver, creds)
        search_jobs(driver, 'Software Engineer')
        apply_to_listings(driver, prefs)
    finally:
        driver.quit()


if __name__ == '__main__':
    main()
