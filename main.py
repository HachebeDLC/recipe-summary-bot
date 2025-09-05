import os
import yt_dlp
import time
import re
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables from .env file
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure the Gemini client
genai.configure(api_key=GEMINI_API_KEY)

def download_video(url):
    """
    Downloads a video from the given URL and returns the path to the video file.
    """
    ydl_opts = {
        'format': 'best',
        'outtmpl': '%(id)s.%(ext)s',
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        video_path = ydl.prepare_filename(info_dict)

    return video_path

def sanitize_markdown(text):
    """
    Sanitizes the text from Gemini to be compliant with Telegram's MarkdownV2.
    This version is more selective to avoid breaking intentional formatting.
    """
    # Replace common bullet points with dashes
    text = text.replace('•', '-')

    # Escape specific characters that are often unescaped by the LLM
    # Note: This is not exhaustive and may need refinement.
    # We are avoiding a blanket escape to preserve formatting like *bold* and _italic_.
    escape_chars = r'.!'
    text = re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

    # Remove trailing backslash if it exists, as it can cause errors
    if text.endswith('\\'):
        text = text[:-1]

    return text

def summarize_video(video_path, language='en'):
    """
    Summarizes the given video into a recipe using the Gemini API.
    """
    # Upload the video file to the Files API
    print(f"Uploading file: {video_path}")
    video_file = genai.upload_file(path=video_path)

    # Wait for the file to be active
    while video_file.state.name == "PROCESSING":
        print("Waiting for file to be processed...")
        time.sleep(10)
        video_file = genai.get_file(name=video_file.name)

    if video_file.state.name != "ACTIVE":
        raise ValueError(f"File {video_file.name} failed to process. Final state: {video_file.state.name}")

    print(f"File {video_file.name} is now active.")

    # Call the Gemini API to summarize the video
    model = genai.GenerativeModel("gemini-2.5-pro")
    prompt = f"""
    Analyze the video provided and generate a detailed recipe.
    The user's preferred language is {language}. All output must be in this language.

    The output should be a well-formatted recipe using Telegram's MarkdownV2 formatting.
    It must include the following sections:

    *A short, engaging description of the dish.*

    *Prep Time:* Estimated preparation time.
    *Cook Time:* Estimated cooking time.
    *Servings:* How many people the recipe serves.

    *Ingredients:*
    - A bulleted list of ingredients. Use the `-` character for bullet points.

    *Instructions:*
    1. A numbered list of clear, step-by-step instructions.

    Take into account all audio and visual information in the video to make the recipe as accurate as possible.
    If the video does not contain a recipe, please respond with only the message "I'm sorry, I couldn't find a recipe in this video." in the requested language.
    """
    response = model.generate_content([prompt, video_file])

    # Clean up the uploaded file
    genai.delete_file(video_file.name)

    return response.text

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command and sets the user's preferred language."""
    # Default language is English
    lang = 'en'

    if context.args:
        lang = context.args[0].lower()
        context.user_data['language'] = lang
        await update.message.reply_text(f"Language set to {lang}. Send me a video link and I'll generate a recipe for you.")
    else:
        context.user_data['language'] = lang
        await update.message.reply_text("Hi! Send me a video link and I'll generate a recipe for you. You can set a language with /start <language_code>, for example, /start es.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles messages that are not commands."""
    url = update.message.text
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Processing your video... This may take a moment.")

    video_path = None
    try:
        # Get user's preferred language, default to 'en'
        language = context.user_data.get('language', 'en')

        video_path = download_video(url)
        raw_summary = summarize_video(video_path, language=language)
        summary = sanitize_markdown(raw_summary)

        try:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=summary, parse_mode=ParseMode.MARKDOWN_V2)
        except Exception as e:
            # If Markdown parsing fails, send as plain text
            await context.bot.send_message(chat_id=update.effective_chat.id, text=raw_summary)

    except Exception as e:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"An error occurred: {e}")
    finally:
        # Clean up the video file
        if video_path and os.path.exists(video_path):
            os.remove(video_path)


def main():
    """Starts the bot."""
    # Check if the necessary API keys are set
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
        print("Please set your Telegram bot token in the .env file.")
        return

    if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
        print("Please set your Gemini API key in the .env file.")
        return

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()

if __name__ == "__main__":
    main()
