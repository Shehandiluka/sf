import os
import tempfile
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from moviepy.editor import *
from PIL import Image

BOT_TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me a photo followed by lyrics (one line per message or a block).")

user_data = {}

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await photo.get_file()
    file_path = tempfile.mktemp(suffix=".jpg")
    await file.download_to_drive(file_path)
    user_data[update.effective_chat.id] = {'image': file_path}
    await update.message.reply_text("Photo received. Now send the lyrics (each line separated by a newline).")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in user_data or 'image' not in user_data[chat_id]:
        await update.message.reply_text("Please send a photo first.")
        return

    lyrics = update.message.text.strip().split("\n")
    user_data[chat_id]['lyrics'] = lyrics

    image_path = user_data[chat_id]['image']
    video_path = tempfile.mktemp(suffix=".mp4")

    await update.message.reply_text("Creating your video...")

    # Create the video
    generate_video(image_path, lyrics, video_path)

    with open(video_path, "rb") as video:
        await update.message.reply_video(video)

def generate_video(image_path, lyrics, output_path):
    duration = 15
    w, h = 1080, 1920
    clip = ImageClip(image_path).resize(height=h).set_duration(duration)
    clip = clip.set_position("center")

    texts = []
    per_line_duration = duration / len(lyrics)

    for i, line in enumerate(lyrics):
        txt = TextClip(line, fontsize=60, color='white', font="Arial-Bold", size=(w - 100, None), method='caption')
        txt = txt.set_duration(per_line_duration).set_start(i * per_line_duration)
        txt = txt.set_position(("center", "center")).crossfadein(0.3).crossfadeout(0.3)
        texts.append(txt)

    final = CompositeVideoClip([clip] + texts, size=(w, h))
    final.write_videofile(output_path, fps=24, codec='libx264', audio=False)

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.run_polling()
