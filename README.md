# Naukri Profile Auto-Updater

This repository contains an automated Python Selenium script that logs into your Naukri profile, navigates to the "Profile Summary" section, and updates the text by dynamically appending or removing a period (`.`) at the end.

Running this script daily keeps your Naukri profile "Active" in the algorithm, pushing your resume higher up in recruiter search results.

## Features

- **Fully Automated:** Runs on GitHub Actions without any manual intervention.
- **Dynamic Text Updating:** Appends a `.` if missing, or removes it if present, ensuring the profile is registered as 'updated' every time.
- **Smart Navigation:** Bypasses skeleton loaders, handles Chatbot popups, and performs a clean UI-based logout.
- **Custom Logging:** Outputs clean, colored logs to both the console and a `naukri.log` file for easy debugging.

---

## Setup Instructions for GitHub Actions

### 1. Clone & Push to Private Repo

Push `naukri_updater.py` and the `.github/workflows/naukri_updater.yml` file to a **Private** GitHub repository to keep your execution logs secure.

### 2. Set Up GitHub Environments & Secrets (CRITICAL)

Your Naukri credentials are required to log in. **Never hardcode your password into the script.** You must pass them securely using GitHub Environment Secrets.

1. Go to your repository on GitHub.
2. Click on **Settings** > **Environments**.
3. Click **New environment**, name it exactly `prod`, and click **Configure environment**.
4. Scroll down to the **Environment secrets** section and click **Add secret**.
5. Add the following two secrets exactly as named:
   - Name: `NAUKRI_EMAIL` | Secret: `your_naukri_email@example.com`
   - Name: `NAUKRI_PASSWORD` | Secret: `your_naukri_password`

### 3. Check Headless Mode

Ensure that the `HEADLESS` variable at the top of your `naukri_updater.py` script is set to `True` before pushing to GitHub. GitHub Actions runs on servers without screens, so the browser must run in the background.

```python
# Set true to run Chrome in headless mode for GitHub Actions
HEADLESS = True
```
