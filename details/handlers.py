import os
import tempfile
import base64
import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode, ChatType
from settings import ANALYZE_CHANNEL_ID, ANALYZE_TOPIC_ID, KASSA_TOPIC_ID, SKLAD_TOPIC_ID, KLIK_TOPIC_ID
from ai import describe_photo, format_cash_message, format_sklad_message, format_klik_message
from pprint import pprint

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Salom, bu bot Moliyaviy guruhlardagi xabarlarni Sun'iy Intellekt yordamida tahlil qilish uchun mo'ljallangan. Tizim hozirda test rejimida ishlamoqda.\nAgar siz MirMaks kompaniyasi filiallari a'zosi bo'lsangiz, iltimos moliya guruhlariga tashlanadigan rasmlarni iloji boricha sifatli qilib olishga harakat qiling.\n\nDeveloper: @BroAZIK"
    )

async def text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular text messages"""
    print(f"Chat ID: {update.effective_chat.id}")
    print(f"Thread ID: {update.message.message_thread_id}")
    
    
    if update.message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
        pass
    else:
        await update.message.reply_text(
        "Salom, bu bot Moliyaviy guruhlardagi xabarlarni Sun'iy Intellekt yordamida tahlil qilish uchun mo'ljallangan. Tizim hozirda test rejimida ishlamoqda.\nAgar siz MirMaks kompaniyasi filiallari a'zosi bo'lsangiz, iltimos moliya guruhlariga tashlanadigan rasmlarni iloji boricha sifatli qilib olishga harakat qiling.\n\nDeveloper: @BroAZIK"
    )

async def analyze_photo_background(bot, chat_id: int, message_id: int, tmp_path: str, sender_name: str, group_name: str, message_link: str) -> None:
    """
    Background task to analyze photo and send results.
    This runs in background so Telegram doesn't timeout.
    """
    try:
        # Read file and convert to base64 for Groq API
        with open(tmp_path, "rb") as f:
            file_data = f.read()
            base64_image = base64.b64encode(file_data).decode("utf-8")
        
        # Analyze the photo using base64 data
        analysis = describe_photo(
            tmp_path,
            "Yuborilgan rasmni tahlil qil va FAQAT JSON formatda natijani qaytarish.",
            f"data:image/jpeg;base64,{base64_image}"
        )
        
        # Determine document type
        doc_type = analysis.get("doc_type", "ignore")
        
        # Ignore unwanted documents
        if doc_type == "ignore":
            # print("Document type is 'ignore', skipping...")
            return
        
        # Select topic ID based on document type
        topic_id_map = {
            "kassa": KASSA_TOPIC_ID,
            "sklad": SKLAD_TOPIC_ID,
            "klik": KLIK_TOPIC_ID
        }
        topic_id = topic_id_map.get(doc_type, ANALYZE_TOPIC_ID)
        
        # Format message based on document type
        if doc_type == "kassa":
            formatted_message = format_cash_message(analysis, group_name, sender_name, message_link)
        elif doc_type == "sklad":
            formatted_message = format_sklad_message(analysis, group_name, sender_name, message_link)
        elif doc_type == "klik":
            formatted_message = format_klik_message(analysis, group_name, sender_name, message_link)
        else:
            return
        
        # Send the formatted message to analytics group with topic
        try:
            result = await bot.send_message(
                chat_id=ANALYZE_CHANNEL_ID,
                message_thread_id=topic_id,
                text=formatted_message,
                parse_mode=ParseMode.HTML
            )
            # print(f"✓ Message sent successfully to topic {topic_id}. Type: {doc_type}")
                
        except Exception as send_error:
            # Fallback: agar topic not found bo'lsa, topic 2'ga jo'nat
            if "thread not found" in str(send_error).lower():
                # print(f"⚠️  Topic {topic_id} not found, trying topic 2 (fallback)...")
                try:
                    await bot.send_message(
                        chat_id=ANALYZE_CHANNEL_ID,
                        message_thread_id=2,
                        text=formatted_message,
                        parse_mode=ParseMode.HTML
                    )
                    # print(f"✓ Message sent successfully to fallback topic 2. Type: {doc_type}")
                except Exception as fallback_error:
                    print(f"✗ Fallback also failed: {fallback_error}")
            else:
                print(f"✗ Failed to send to channel {ANALYZE_CHANNEL_ID}: {send_error}")
            
    except Exception as e:
        print(f"✗ Error in background analysis: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up temporary file
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
                # print(f"✓ Temporary file deleted: {tmp_path}")
        except Exception as cleanup_error:
            print(f"Could not delete temporary file: {cleanup_error}")

async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle photo messages quickly - start background analysis.
    Responds immediately to avoid Telegram timeout.
    """
    try:
        # Get sender info
        sender_name = update.message.from_user.full_name or update.message.from_user.username or "Unknown"
        group_name = update.effective_chat.title or "Group"
        
        # Store chat and message IDs for later use in background task
        chat_id = update.effective_chat.id
        message_id = update.message.message_id
        
        # Get message link (for topic channels, this includes the topic ID)
        message_link = f"https://t.me/c/{str(chat_id)[4:]}/{message_id}"
        
        # Get the photo (highest quality)
        photo_file = update.message.photo[-1]
        
        print(f"📥 Rasm qabul qilindi: {sender_name} ({group_name})")
        
        # Download the photo to a temporary file
        temp_file = await context.bot.get_file(photo_file.file_id)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp_path = tmp.name
            # Download file data
            file_data = await temp_file.download_as_bytearray()
            tmp.write(file_data)
        
        print(f"⏳ Tahlil qilinyapti... ({tmp_path})")
        
        # Start background analysis task (don't wait for it)
        # Use create_task to avoid blocking the handler
        context.application.create_task(
            analyze_photo_background(
                context.bot,
                chat_id,
                message_id,
                tmp_path,
                sender_name,
                group_name,
                message_link
            )
        )
        await update.message.set_reaction("👍")
        # print(f"✓ Background task started for: {tmp_path}")
            
    except Exception as e:
        # print(f"Error processing photo: {e}")
        import traceback
        traceback.print_exc()


async def handle_album(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle album/media group - process each photo individually.
    This is called when update.message.media_group_id is present.
    """
    if not hasattr(update.message, 'media_group_id'):
        return
    
    # Get all photos from the media group from context
    media_group_id = update.message.media_group_id
    
    # Process each photo in the album
    if update.message.photo:
        await photo(update, context)