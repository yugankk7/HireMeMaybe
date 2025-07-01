"""Basic script to automate applying to jobs on Naukri.com using Selenium."""

from dataclasses import dataclass
import os
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
    location: str
    salary_range: str


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
    ).format(title=job_title, location=prefs.location, salary=prefs.salary_range, resume=resume)
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
        )
        return resp.choices[0].message.content.strip()
    except Exception as exc:
        print(f"OpenAI API error: {exc}")
        return ""


def apply_to_listings(driver: webdriver.Chrome, prefs: JobPreferences, resume: str) -> None:
    """Iterate through job listings and apply to each one."""
    jobs = driver.find_elements(By.CSS_SELECTOR, 'article.jobTuple')
    for job in jobs:
        try:
            title_el = job.find_element(By.CSS_SELECTOR, 'a.title')
            job_title = title_el.text
            cover_letter = generate_cover_letter(job_title, prefs, resume)
            print(f"Cover letter for {job_title}:\n{cover_letter}\n")

            apply_btn = job.find_element(By.CSS_SELECTOR, 'button.btn-apply')
            apply_btn.click()
            # Additional steps such as uploading resume or filling forms would go here
            time.sleep(2)
            driver.back()
        except Exception as exc:
            print(f'Skipping listing due to error: {exc}')


def main() -> None:
    creds = Credentials(
        username='your_username',
        password='your_password',
        resume_path='/path/to/resume.pdf'
    )
    prefs = JobPreferences(
        location='Bangalore',
        salary_range='10-12 LPA'
    )

    resume_text = load_resume(creds.resume_path)

    driver = create_driver()
    try:
        login(driver, creds)
        search_jobs(driver, 'Software Engineer')
        apply_to_listings(driver, prefs, resume_text)
    finally:
        driver.quit()


if __name__ == '__main__':
    main()
