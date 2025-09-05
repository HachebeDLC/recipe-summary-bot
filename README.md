# Recipe Bot

A Telegram bot that downloads videos from social media, transcribes the audio, and uses AI to generate a recipe summary.

## Features

*   Downloads videos from YouTube, TikTok, and other social media sites.
*   Extracts the audio from the video.
*   Transcribes the audio using Google's Gemini Pro model.
*   Summarizes the recipe using Google's Gemini Pro model.

## Prerequisites

Before you can run this bot, you will need the following:

*   A Telegram account.
*   A Google AI Studio account.

## Setup

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/your-username/recipe-bot.git
    cd recipe-bot
    ```

2.  **Create a virtual environment and install the dependencies:**

    ```bash
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **Create a `.env` file:**

    Create a file named `.env` in the root of the project and add the following content:

    ```
    TELEGRAM_BOT_TOKEN="YOUR_TELEGRAM_BOT_TOKEN"
    GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
    ```

4.  **Get the API Keys:**

    *   **Telegram Bot Token:** Talk to the [BotFather](https://t.me/botfather) on Telegram to create a new bot and get the token.
    *   **Gemini API Key:** Go to [Google AI Studio](https://aistudio.google.com/) and create a new API key.

    Replace the placeholder values in the `.env` file with your actual API keys.

## Deployment

You can deploy this bot using Docker.

1.  **Build the Docker image:**

    ```bash
    docker build -t recipe-bot .
    ```

2.  **Run the Docker container:**

    ```bash
    docker run -d --env-file .env recipe-bot
    ```

    The bot will now be running in the background.

## Usage

1.  Start a chat with your bot on Telegram.
2.  Send it a link to a video from YouTube, TikTok, or any other supported site.
3.  The bot will process the video and send you a recipe summary.