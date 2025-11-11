# Job Alert Bot 🤖

This is an automated bot that scrapes IT job postings from multiple sources, processes them through an advanced filtering and scoring system, and notifies the most relevant results to a Telegram channel.

The main goal is to filter out the "noise" from job portals and present only the offers that fit a specific search profile, which is easily configurable (by default, it's set for entry-level roles). This project also serves as a data backend for a separate web application.

## ✨ Key Features

-   **Multi-Source Scraping**: Fetches jobs from **Get on Board**, **Educación IT**, **Empleos IT**, and **JobSpy** (which in turn scrapes LinkedIn, Indeed, and others).
-   **Firestore Database**: Uses Google Firestore to store processed jobs, preventing duplicate notifications and tracking data over time.
-   **Advanced Filtering**:
    -   Automatically discards jobs from non-IT related fields (e.g., HR, Marketing, Finance).
    -   Excludes roles that do not match the desired seniority level (e.g., Senior, Lead, Manager).
-   **Scoring System**:
    -   Each job is run through an algorithm that assigns a relevance score from 0 to 100.
    -   The system analyzes the job title and description for keywords related to technologies, roles, and seniority.
    -   Applies bonuses and penalties based on configurable rules.
-   **Tag Generation**: Extracts and assigns the most important keywords to each job (e.g., `react`, `python`, `aws`, `backend`) for easy identification.
-   **Telegram Notifications**: Sends jobs that exceed a minimum score threshold to a designated Telegram channel.
-   **Web Frontend Integration**: Triggers a cache revalidation on a separate web application to keep its data up-to-date.
-   **Automated Execution**: Designed to be run automatically via **GitHub Actions** on a schedule.

## ⚙️ How It Works (Workflow)

1.  **Scrape**: The bot runs and fetches the latest job postings from all enabled sources.
2.  **Deduplication**: It checks Firestore to see if the jobs have already been processed.
3.  **Pre-filtering**: Applies a first layer of filters to discard jobs based on area and undesired seniority.
4.  **Scoring & Final Filtering**: Assigns a score to the remaining jobs. Only those that surpass the `MIN_SCORE` are accepted.
5.  **Notification**: Accepted jobs are sent to the Telegram channel.
6.  **Storage**: All processed jobs (both accepted and rejected) are saved to Firestore for future reference and deduplication.
7.  **Cache Revalidation**: A request is sent to the web frontend to revalidate its cache, ensuring the new job data is reflected.

## 🚀 Getting Started

### Prerequisites

-   Python 3.11 or higher
-   A Google Cloud project with Firestore enabled
-   A Telegram Bot Token and Channel ID

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/job-alert-bot.git
    cd job-alert-bot
    ```

2.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## 🔧 Configuration

The project is configured through environment variables. You can create a `.env` file in the project root to manage them locally.

### Core Configuration

-   `BOT_TOKEN` (Required): Your Telegram bot token.
-   `TELEGRAM_CHANNEL_ID` (Required): The ID of the Telegram channel where notifications will be sent.

### Job Sources

-   `JOB_SOURCES`: A comma-separated list of sources to use. If not set, all available sources will be used.
    -   **Available Sources**: `getonboard`, `educacionit`, `jobspy`, `empleosit`
    -   **Example**: `JOB_SOURCES=getonboard,jobspy`

### Firebase/Google Cloud

-   `GOOGLE_APPLICATION_CREDENTIALS`: The absolute path to your Google Cloud service account JSON key file. This is required for local development. When deployed (e.g., on GitHub Actions), you might use a different authentication method (like Workload Identity Federation or a base64-encoded secret).

### Web Frontend Integration

-   `BASE_URL`: The base URL of the web application to trigger cache revalidation.
-   `REVALIDATION_SECRET`: The secret token required by the frontend's revalidation endpoint.

## ▶️ Usage

To run the bot manually:

1.  **Set up your environment variables:**
    -   Create a `.env` file with the necessary variables (see Configuration section).
    -   Or export them in your shell:
    ```bash
    export BOT_TOKEN="YOUR_TELEGRAM_BOT_TOKEN"
    export TELEGRAM_CHANNEL_ID="YOUR_TELEGRAM_CHANNEL_ID"
    export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/credentials.json"
    export JOB_SOURCES="getonboard,jobspy"
    ```

2.  **Run the main script:**
    ```bash
    python main.py
    ```

The bot is also designed to be run automatically. The `.github/workflows/scraper.yml` file contains a GitHub Actions workflow to run the script on a schedule.

## 🛠️ Tech Stack

-   **Language**: Python 3.11
-   **Scraping**: `requests`, `beautifulsoup4`, `python-jobspy`
-   **Database**: Google Firestore
-   **Notifications**: `python-telegram-bot`
-   **Orchestration**: GitHub Actions
-   **Data Handling**: `pandas`, `dateparser`
