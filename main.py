import os
import yt_dlp
from telegram import Update
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

def summarize_video(video_path):
    """
    Summarizes the given video into a recipe using the Gemini API.
    """
    # Upload the video file to the Files API
    video_file = genai.upload_file(path=video_path)

    # Call the Gemini API to summarize the video
    model = genai.GenerativeModel("gemini-2.5-pro")
    prompt = """
    Analyze the video and generate a recipe.
    The output should be a well-formatted recipe with a title, a list of ingredients, and step-by-step instructions.
    Take into account both the audio and visual information in the video.
    If the video does not contain a recipe, please indicate that.
    """
    response = model.generate_content([prompt, video_file])

    # Clean up the uploaded file
    genai.delete_file(video_file.name)

    return response.text

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a welcome message when the /start command is issued."""
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Hi! Send me a video link and I'll generate a recipe for you.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles messages that are not commands."""
    url = update.message.text
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Processing your video... This may take a moment.")

    video_path = None
    try:
        video_path = download_video(url)
        summary = summarize_video(video_path)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=summary)
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
