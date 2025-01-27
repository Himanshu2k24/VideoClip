import os
from flask import Flask
from threading import Thread
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from telegram.ext import Updater, MessageHandler, filters, CommandHandler

app = Flask(__name__)

def split_video(update, context):
    user = update.message.from_user
    video_file = update.message.video or update.message.document

    if not video_file:
        update.message.reply_text("Please send a valid video file.")
        return

    # Download the video file
    video_file_path = context.bot.get_file(video_file.file_id).download()
    update.message.reply_text("Processing your video...")

    try:
        video = VideoFileClip(video_file_path)
        duration = int(video.duration)
        part = 1
        clips = []

        for start in range(0, duration, 45):
            end = min(start + 45, duration)
            subclip = video.subclip(start, end)

            # Add watermark text
            watermark_text = TextClip(f"Part {part}", fontsize=50, color="white")
            watermark_text = watermark_text.set_position(("center", 50)).set_duration(subclip.duration)

            watermarked_clip = CompositeVideoClip([subclip, watermark_text])

            # Save the clip
            output_file = f"part_{part}.mp4"
            watermarked_clip.write_videofile(output_file, codec="libx264", audio_codec="aac")

            clips.append(output_file)
            part += 1

        # Send the clips back to the user
        for clip in clips:
            with open(clip, "rb") as video:
                context.bot.send_video(chat_id=update.message.chat_id, video=video)

        # Cleanup
        video.close()
        for clip in clips:
            os.remove(clip)

    except Exception as e:
        update.message.reply_text(f"Error: {e}")

    finally:
        os.remove(video_file_path)

def start(update, context):
    update.message.reply_text("Welcome! Send me a video, and I'll split it into 45-second parts with watermarks.")

def run_telegram_bot():
    API_TOKEN = "7729792798:AAFCEjMfSMqy9tpXw0SPGJ5QC1rW5DqkazU"

    updater = Updater(API_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(filters.Video | filters.Document, split_video))

    updater.start_polling()
    updater.idle()

@app.route("/")
def health_check():
    return "Bot is running!"

if __name__ == "__main__":
    # Start Flask app in a separate thread to allow health checks
    Thread(target=run_telegram_bot).start()
    app.run(host="0.0.0.0", port=8000)
