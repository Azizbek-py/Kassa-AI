#!/usr/bin/env python3
"""
Test script to verify channel ID and send a test message.
"""
import asyncio
from telegram import Bot
from settings import BOT_TOKEN, ANALYZE_CHANNEL_ID, ANALYZE_TOPIC_ID

async def test_channel():
    bot = Bot(token=BOT_TOKEN)
    
    print("=" * 50)
    print("CHANNEL ID TEST")
    print("=" * 50)
    print(f"BOT_TOKEN: {BOT_TOKEN[:20]}...")
    print(f"ANALYZE_CHANNEL_ID: {ANALYZE_CHANNEL_ID}")
    print(f"ANALYZE_TOPIC_ID: {ANALYZE_TOPIC_ID}")
    print()
    
    # Try to get bot info
    try:
        me = await bot.get_me()
        print(f"✓ Bot connected successfully: {me.first_name} (@{me.username})")
    except Exception as e:
        print(f"✗ Bot connection failed: {e}")
        return
    
    print()
    print("Attempting to send test message...")
    print("-" * 50)
    
    # Try sending test message
    try:
        message = await bot.send_message(
            chat_id=ANALYZE_CHANNEL_ID,
            message_thread_id=ANALYZE_TOPIC_ID,
            text="🧪 Test message - Bot is working!"
        )
        print(f"✓ Message sent successfully!")
        print(f"  Message ID: {message.message_id}")
        print(f"  Chat ID: {message.chat_id}")
        print(f"  Topic ID: {message.message_thread_id}")
    except Exception as e:
        print(f"✗ Failed to send message: {e}")
        print()
        print("TROUBLESHOOTING STEPS:")
        print("-" * 50)
        print("1. Verify channel ID:")
        print("   - Open channel in Telegram Desktop")
        print("   - Right-click → Copy Link")
        print("   - Format: https://t.me/c/CHANNEL_ID/TOPIC_ID")
        print()
        print("2. Check bot permissions:")
        print("   - Add bot to the channel")
        print("   - Make bot an admin")
        print("   - Give 'Send Messages' permission")
        print()
        print("3. Update settings.py with correct IDs")
        print()
        print("ERROR DETAILS:")
        print(str(e))

if __name__ == "__main__":
    asyncio.run(test_channel())
