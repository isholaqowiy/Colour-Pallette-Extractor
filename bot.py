import os
import io
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from PIL import Image

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("BOT_TOKEN")

user_images = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to Image Flip/Rotate Bot!\n\n"
        "📸 Send me any image and I'll give you options to:\n"
        "• Rotate 90°, 180°, 270°\n"
        "• Flip Horizontally\n"
        "• Flip Vertically"
    )

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    photo = update.message.photo[-1] if update.message.photo else None
    document = update.message.document if update.message.document else None

    if photo:
        file = await photo.get_file()
    elif document and document.mime_type and document.mime_type.startswith("image/"):
        file = await document.get_file()
    else:
        await update.message.reply_text("❌ Please send a valid image file.")
        return

    file_bytes = await file.download_as_bytearray()
    user_images[user_id] = bytes(file_bytes)

    keyboard = [
        [
            InlineKeyboardButton("↩️ Rotate 90°", callback_data="rotate_90"),
            InlineKeyboardButton("🔄 Rotate 180°", callback_data="rotate_180"),
        ],
        [
            InlineKeyboardButton("↪️ Rotate 270°", callback_data="rotate_270"),
            InlineKeyboardButton("↔️ Flip Horizontal", callback_data="flip_horizontal"),
        ],
        [
            InlineKeyboardButton("↕️ Flip Vertical", callback_data="flip_vertical"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("✅ Image received! Choose an action:", reply_markup=reply_markup)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    if user_id not in user_images:
        await query.edit_message_text("❌ No image found. Please send an image first.")
        return

    img_bytes = user_images[user_id]
    image = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
    action = query.data

    if action == "rotate_90":
        result = image.rotate(90, expand=True)
        caption = "↩️ Rotated 90°"
    elif action == "rotate_180":
        result = image.rotate(180, expand=True)
        caption = "🔄 Rotated 180°"
    elif action == "rotate_270":
        result = image.rotate(270, expand=True)
        caption = "↪️ Rotated 270°"
    elif action == "flip_horizontal":
        result = image.transpose(Image.FLIP_LEFT_RIGHT)
        caption = "↔️ Flipped Horizontally"
    elif action == "flip_vertical":
        result = image.transpose(Image.FLIP_TOP_BOTTOM)
        caption = "↕️ Flipped Vertically"
    else:
        await query.edit_message_text("❌ Unknown action.")
        return

    output = io.BytesIO()
    result = result.convert("RGB")
    result.save(output, format="PNG")
    output.seek(0)

    await query.edit_message_text("✅ Done! Sending your image...")
    await context.bot.send_photo(
        chat_id=query.message.chat_id,
        photo=output,
        caption=caption
    )

    keyboard = [
        [
            InlineKeyboardButton("↩️ Rotate 90°", callback_data="rotate_90"),
            InlineKeyboardButton("🔄 Rotate 180°", callback_data="rotate_180"),
        ],
        [
            InlineKeyboardButton("↪️ Rotate 270°", callback_data="rotate_270"),
            InlineKeyboardButton("↔️ Flip Horizontal", callback_data="flip_horizontal"),
        ],
        [
            InlineKeyboardButton("↕️ Flip Vertical", callback_data="flip_vertical"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="🔁 Apply another transformation to the original image:",
        reply_markup=reply_markup
    )

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, handle_image))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.run_polling()

if __name__ == "__main__":
    main()
