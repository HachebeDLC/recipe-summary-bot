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