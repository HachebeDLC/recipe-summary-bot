# Recipe Bot

A Telegram bot that downloads videos from social media and uses AI to generate a recipe summary directly from the video content.

## Features

*   Downloads videos from YouTube, TikTok, and other social media sites.
*   Analyzes the video content (both audio and visual) using Google's Gemini Pro model.
*   Generates a well-formatted recipe summary from the video.
*   Supports multiple languages for the recipe output.
*   Remembers your language preference between restarts.
*   Formats the recipe summary using Markdown for better readability.

## Prerequisites

Before you can run this bot, you will need the following:

*   A Telegram account.
*   A Google AI Studio account.
*   Docker and Docker Compose installed on your machine.

## Setup

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/your-username/recipe-bot.git
    cd recipe-bot
    ```

2.  **Create a `.env` file:**

    Create a file named `.env` in the root of the project by copying the example:

    ```bash
    cp .env.example .env
    ```

    Then, edit the `.env` file to set your secrets. It should look like this:

    ```
    TELEGRAM_BOT_TOKEN="YOUR_TELEGRAM_BOT_TOKEN"
    GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
    MONGO_USER="user"
    MONGO_PASS="password"
    MONGO_URI="mongodb://${MONGO_USER}:${MONGO_PASS}@mongo:27017/"
    ```

    *   Set your `TELEGRAM_BOT_TOKEN` and `GEMINI_API_KEY`.
    *   You can change the default `MONGO_USER` and `MONGO_PASS` to something more secure.
    *   The `MONGO_URI` is automatically constructed from the user and pass, and should not need to be changed.

## Deployment

The easiest way to run the bot is with Docker Compose. This will start the bot and a local MongoDB database for caching.

1.  **Start the application:**

    ```bash
    docker-compose up --build -d
    ```

    The `-d` flag runs the containers in the background.

2.  **To stop the application:**

    ```bash
    docker-compose down
    ```

## Usage

1.  Start a chat with your bot on Telegram.
2.  (Optional) Set your preferred language by sending the command `/start <language_code>`. For example, `/start es` for Spanish. If you don't set a language, it will default to English.
3.  Send it a link to a video from YouTube, TikTok, or any other supported site.
4.  The bot will process the video and send you a recipe summary, formatted for readability.

---

## CI/CD Deployment with GitHub Actions and Tailscale

This project includes a GitHub Actions workflow to automatically deploy the bot to an on-premise server every time you push to the `main` branch.

### On-Premise Server Setup

Your server needs the following software installed:
*   Docker
*   Docker Compose
*   Git
*   Tailscale
*   An SSH server (like OpenSSH)

You must also:
1.  Install Tailscale on the server and ensure it's connected to your Tailnet.
2.  Clone this repository to a directory on the server (e.g., `~/recipe-bot`). The deployment script assumes this location.
3.  Generate an SSH key pair on your local machine (not the server): `ssh-keygen -t ed25519 -C "your_email@example.com"`.
4.  Copy the contents of the public key (e.g., `~/.ssh/id_ed25519.pub`) and add it to the `~/.ssh/authorized_keys` file on your on-premise server.

### GitHub Secrets Configuration

For the GitHub Actions workflow to run, you must configure the following secrets in your GitHub repository's settings (`Settings > Secrets and variables > Actions`):

*   **`TAILSCALE_AUTHKEY`**: A Tailscale auth key. It is highly recommended to use an ephemeral, pre-authorized, and tagged key for security. Generate one in your Tailscale Admin Console under `Settings > Keys`.
*   **`SSH_HOST`**: The Tailscale IP address or magic DNS name of your on-premise server.
*   **`SSH_USER`**: The username you will use to SSH into your on-premise server.
*   **`SSH_PRIVATE_KEY`**: The contents of the private SSH key you generated earlier (e.g., the content of the `~/.ssh/id_ed25519` file).

Once these steps are completed, any push to the `main` branch will automatically trigger the deployment workflow.