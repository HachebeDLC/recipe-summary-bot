import os
import yt_dlp
from moviepy.editor import *
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import google.generativeai as genai
import assemblyai as aai

# Load environment variables from .env file
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")

# Configure the Gemini and AssemblyAI clients
genai.configure(api_key=GEMINI_API_KEY)
aai.settings.api_key = ASSEMBLYAI_API_KEY

def download_and_extract_audio(url):
    """
    Downloads a video from the given URL, extracts the audio,
    and returns the path to the audio file.
    """
    ydl_opts = {
        'format': 'best',
        'outtmpl': '%(id)s.%(ext)s',
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        video_path = ydl.prepare_filename(info_dict)

    video = VideoFileClip(video_path)
    audio_path = os.path.splitext(video_path)[0] + '.mp3'
    video.audio.write_audiofile(audio_path)

    os.remove(video_path)

    return audio_path

def transcribe_audio(audio_file_path):
    """
    Transcribes the given audio file using AssemblyAI.
    """
    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(audio_file_path)

    if transcript.status == aai.TranscriptStatus.error:
        raise Exception(f"AssemblyAI transcription failed: {transcript.error}")
    else:
        return transcript.text

def summarize_text(text):
    """
    Summarizes the given text into a recipe using Gemini.
    """
    model = genai.GenerativeModel("gemini-1.5-pro-preview-0409")
    prompt = f"""
    Please analyze the following text and extract a recipe from it.
    The output should be a well-formatted recipe with a title, a list of ingredients, and step-by-step instructions.
    If the text does not contain a recipe, please indicate that.

    Text:
    {text}
    """
    response = model.generate_content(prompt)
    return response.text

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a welcome message when the /start command is issued."""
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Hi! Send me a video link and I'll summarize the recipe for you.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles messages that are not commands."""
    url = update.message.text
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Processing your video...")

    try:
        audio_file = download_and_extract_audio(url)
        transcript = transcribe_audio(audio_file)
        summary = summarize_text(transcript)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=summary)
    except Exception as e:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"An error occurred: {e}")
    finally:
        # Clean up the audio file
        if 'audio_file' in locals() and os.path.exists(audio_file):
            os.remove(audio_file)


def main():
    """Starts the bot."""
    # Check if the necessary API keys are set
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
        print("Please set your Telegram bot token in the .env file.")
        return

    if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
        print("Please set your Gemini API key in the .env file.")
        return

    if not ASSEMBLYAI_API_KEY or ASSEMBLYAI_API_KEY == "YOUR_ASSEMBLYAI_API_KEY":
        print("Please set your AssemblyAI API key in the .env file.")
        return

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()

if __name__ == "__main__":
    main()
