import os
import yt_dlp
import time
import json
import re
import asyncio
from datetime import datetime
import pymongo
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

# Configure MongoDB connection
MONGO_URI = os.getenv("MONGO_URI")
mongo_client = pymongo.MongoClient(MONGO_URI)
db = mongo_client.recipe_bot
recipes_collection = db.recipes
user_preferences_collection = db.user_preferences

# Internationalization (i18n) strings
MESSAGES = {
    'en': {
        'welcome': "Hi! Send me a video link and I'll generate a recipe for you. Your current language is English. You can set a new one with /start <language_code> (e.g., /start es).",
        'lang_set': "Language set to {language}. Send me a video link and I'll generate a recipe for you.",
        'processing': "Processing your video... This may take a moment.",
        'from_cache': "Found this recipe in the cache! Here you go:",
        'error': "An error occurred: {error}",
        'no_recipe': "I'm sorry, I couldn't find a recipe in this video."
    },
    'es': {
        'welcome': "¡Hola! Envíame un enlace de video y te generaré una receta. Tu idioma actual es Español. Puedes configurar uno nuevo con /start <código_de_idioma> (ej. /start en).",
        'lang_set': "Idioma configurado a {language}. Envíame un enlace de video y te generaré una receta.",
        'processing': "Procesando tu video... Esto puede tardar un momento.",
        'from_cache': "¡Encontré esta receta en el caché! Aquí tienes:",
        'error': "Ocurrió un error: {error}",
        'no_recipe': "Lo siento, no pude encontrar una receta en este video."
    }
}

def get_message(language, key, **kwargs):
    """Gets a localized message string."""
    # Fallback to English if the language or key doesn't exist
    lang_messages = MESSAGES.get(language, MESSAGES['en'])
    message = lang_messages.get(key, MESSAGES['en'].get(key, "Message key not found."))
    return message.format(**kwargs)

def get_user_language(user_id):
    """Gets the user's language from MongoDB, defaulting to 'en'."""
    user_pref = user_preferences_collection.find_one({"user_id": user_id})
    return user_pref.get("language", "en") if user_pref else "en"

def set_user_language(user_id, language):
    """Sets the user's language in MongoDB."""
    user_preferences_collection.update_one(
        {"user_id": user_id},
        {"$set": {"language": language}},
        upsert=True
    )

def get_cached_recipe(url, language):
    """Checks the MongoDB cache for a recipe."""
    print(f"Checking cache for URL: {url} and language: {language}")
    return recipes_collection.find_one({"url": url, "language": language})

def cache_recipe(url, language, recipe_data):
    """Caches a new recipe in MongoDB."""
    print(f"Caching recipe for URL: {url} and language: {language}")
    document = {
        "url": url,
        "language": language,
        "recipe_data": recipe_data,
        "timestamp": datetime.utcnow()
    }
    recipes_collection.insert_one(document)

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

def escape_markdown_v2(text):
    """Escapes strings for Telegram's MarkdownV2."""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

def format_recipe_markdown(recipe_data):
    """Formats the recipe data from a dictionary into a MarkdownV2 string."""
    markdown_parts = []

    title = escape_markdown_v2(recipe_data.get("title", "Untitled Recipe"))
    markdown_parts.append(f"*{title}*")

    description = escape_markdown_v2(recipe_data.get("description", ""))
    if description:
        markdown_parts.append(f"_{description}_")

    prep_time = escape_markdown_v2(recipe_data.get("prep_time", "N/A"))
    cook_time = escape_markdown_v2(recipe_data.get("cook_time", "N/A"))
    servings = escape_markdown_v2(recipe_data.get("servings", "N/A"))
    markdown_parts.append(f"*Prep Time:* {prep_time}\n*Cook Time:* {cook_time}\n*Servings:* {servings}")

    ingredients = recipe_data.get("ingredients", [])
    if ingredients:
        markdown_parts.append("*Ingredients:*")
        ingredient_list = [f"\\- {escape_markdown_v2(item)}" for item in ingredients]
        markdown_parts.append("\n".join(ingredient_list))

    instructions = recipe_data.get("instructions", [])
    if instructions:
        markdown_parts.append("*Instructions:*")
        instruction_list = [f"{i+1}\\. {escape_markdown_v2(item)}" for i, item in enumerate(instructions)]
        markdown_parts.append("\n".join(instruction_list))

    return "\n\n".join(markdown_parts)

def summarize_video(video_path, language='en'):
    """
    Sends a video to the Gemini API and asks for a recipe in JSON format.
    Returns a dictionary parsed from the JSON response.
    """
    print(f"Uploading file: {video_path}")
    video_file = genai.upload_file(path=video_path)

    while video_file.state.name == "PROCESSING":
        print("Waiting for file to be processed...")
        time.sleep(10)
        video_file = genai.get_file(name=video_file.name)

    if video_file.state.name != "ACTIVE":
        raise ValueError(f"File {video_file.name} failed to process. Final state: {video_file.state.name}")

    print(f"File {video_file.name} is now active.")

    model = genai.GenerativeModel("gemini-2.5-pro")
    prompt = f"""
    Analyze the video provided and generate a detailed recipe.
    The user's preferred language is {language}. All output must be in this language.

    Your response MUST be a single JSON object. Do not include any text outside of the JSON object.
    The JSON object should have the following keys: "title", "description", "prep_time", "cook_time", "servings", "ingredients" (an array of strings), and "instructions" (an array of strings).

    If the video does not contain a recipe, return a JSON object with a single key "error" with the value "No recipe found".
    """

    response = model.generate_content([prompt, video_file])
    genai.delete_file(video_file.name)

    # Clean up the response and parse the JSON
    clean_response = response.text.strip().replace("```json", "").replace("```", "")
    try:
        recipe_data = json.loads(clean_response)
        return recipe_data
    except json.JSONDecodeError:
        # Handle cases where the response is not valid JSON
        raise ValueError("Failed to parse recipe data from the AI's response.")

MAX_MESSAGE_LENGTH = 4096

async def send_long_message(bot, chat_id, text, parse_mode=None):
    """Splits a long message into multiple parts and sends them."""
    if len(text) <= MAX_MESSAGE_LENGTH:
        await bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode)
        return

    parts = []
    current_part = ""
    for line in text.split('\n'):
        if len(current_part) + len(line) + 1 > MAX_MESSAGE_LENGTH:
            parts.append(current_part)
            current_part = line
        else:
            if current_part:
                current_part += "\n" + line
            else:
                current_part = line

    if current_part:
        parts.append(current_part)

    for part in parts:
        await bot.send_message(chat_id=chat_id, text=part, parse_mode=parse_mode)
        await asyncio.sleep(1) # Small delay to ensure messages arrive in order

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command and sets the user's preferred language."""
    user_id = update.effective_user.id
    lang = get_user_language(user_id) # Get current language first

    if context.args:
        new_lang = context.args[0].lower()
        if new_lang in MESSAGES:
            set_user_language(user_id, new_lang)
            # Use the new language for the confirmation message
            await update.message.reply_text(get_message(new_lang, 'lang_set', language=new_lang))
        else:
            await update.message.reply_text(f"Sorry, '{new_lang}' is not a supported language code.")
    else:
        # If no args, just send the welcome message in the user's current language
        await update.message.reply_text(get_message(lang, 'welcome'))


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles messages that are not commands."""
    url = update.message.text
    user_id = update.effective_user.id
    language = get_user_language(user_id)

    # Check cache first
    cached_recipe = get_cached_recipe(url, language)
    if cached_recipe:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=get_message(language, 'from_cache'))
        summary = format_recipe_markdown(cached_recipe['recipe_data'])
        await send_long_message(context.bot, update.effective_chat.id, summary, parse_mode=ParseMode.MARKDOWN_V2)
        return

    await context.bot.send_message(chat_id=update.effective_chat.id, text=get_message(language, 'processing'))

    video_path = None
    try:
        video_path = download_video(url)
        recipe_data = summarize_video(video_path, language=language)

        if "error" in recipe_data:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=get_message(language, 'no_recipe'))
        else:
            # Cache the new recipe
            cache_recipe(url, language, recipe_data)
            summary = format_recipe_markdown(recipe_data)
            await send_long_message(context.bot, update.effective_chat.id, summary, parse_mode=ParseMode.MARKDOWN_V2)

    except Exception as e:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=get_message(language, 'error', error=e))
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
