

import logging
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import Config
from Database.database import Seishiro
from Plugins.helper import user_states, WAITING_DUMP_CHANNEL
from datetime import datetime

logger = logging.getLogger(__name__)

# Log channel management
@Client.on_message(filters.command("setlogchannel") & filters.private)
async def set_log_channel(client, message):
    """Set the log channel for bot activities"""
    if message.from_user.id != Config.USER_ID:
        await message.reply("❌ This command is owner-only.")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        await message.reply(
            "<b>📝 Set Log Channel</b>\n\n"
            "<b>Usage:</b> <code>/setlogchannel [channel_id]</code>\n\n"
            "<b>Example:</b> <code>/setlogchannel -1001234567890</code>\n\n"
            "<i>💡 Forward a message from the channel to get its ID</i>",
            parse_mode=enums.ParseMode.HTML
        )
        return
    
    try:
        channel_id = int(parts[1])
        
        # Test if bot has access to the channel
        try:
            chat = await client.get_chat(channel_id)
            if chat.type not in ["channel", "supergroup"]:
                await message.reply("❌ Please provide a channel or supergroup ID.")
                return
        except Exception as e:
            await message.reply(f"❌ Cannot access channel. Make sure the bot is added as admin.\n\nError: {e}")
            return
        
        # Save to database
        if await Seishiro.set_config("log_channel", channel_id):
            await message.reply(
                f"✅ <b>Log Channel Set!</b>\n\n"
                f"<b>Channel:</b> {chat.title}\n"
                f"<b>ID:</b> <code>{channel_id}</code>\n\n"
                f"<i>All bot activities will be logged here.</i>",
                parse_mode=enums.ParseMode.HTML
            )
            
            # Send test message to log channel
            await client.send_message(
                channel_id,
                f"📊 <b>Log Channel Activated</b>\n\n"
                f"<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"<b>Set by:</b> {message.from_user.mention}\n\n"
                f"<i>This channel will now receive all bot activity logs.</i>",
                parse_mode=enums.ParseMode.HTML
            )
        else:
            await message.reply("❌ Failed to save log channel to database.")
    
    except ValueError:
        await message.reply("❌ Invalid channel ID. Please provide a numeric ID.")
    except Exception as e:
        logger.error(f"Error setting log channel: {e}")
        await message.reply(f"❌ Error: {e}")


@Client.on_message(filters.command("removelogchannel") & filters.private)
async def remove_log_channel(client, message):
    """Remove the log channel"""
    if message.from_user.id != Config.USER_ID:
        await message.reply("❌ This command is owner-only.")
        return
    
    current_log = await Seishiro.get_config("log_channel")
    if not current_log:
        await message.reply("❌ No log channel is currently set.")
        return
    
    if await Seishiro.set_config("log_channel", None):
        await message.reply("✅ Log channel removed successfully.")
    else:
        await message.reply("❌ Failed to remove log channel.")


# Dump channel management
@Client.on_message(filters.command("setdumpchannel") & filters.private)
async def set_dump_channel(client, message):
    """Set the dump channel for file backups"""
    if message.from_user.id != Config.USER_ID:
        await message.reply("❌ This command is owner-only.")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        await message.reply(
            "<b>💾 Set Dump Channel</b>\n\n"
            "<b>Usage:</b> <code>/setdumpchannel [channel_id]</code>\n\n"
            "<b>Example:</b> <code>/setdumpchannel -1001234567890</code>\n\n"
            "<i>💡 This channel will store backup copies of all uploaded files</i>",
            parse_mode=enums.ParseMode.HTML
        )
        return
    
    try:
        channel_id = int(parts[1])
        
        # Test if bot has access to the channel
        try:
            chat = await client.get_chat(channel_id)
            if chat.type not in ["channel", "supergroup"]:
                await message.reply("❌ Please provide a channel or supergroup ID.")
                return
        except Exception as e:
            await message.reply(f"❌ Cannot access channel. Make sure the bot is added as admin.\n\nError: {e}")
            return
        
        # Save to database
        if await Seishiro.set_config("dump_channel", channel_id):
            await message.reply(
                f"✅ <b>Dump Channel Set!</b>\n\n"
                f"<b>Channel:</b> {chat.title}\n"
                f"<b>ID:</b> <code>{channel_id}</code>\n\n"
                f"<i>All uploaded files will be backed up here.</i>",
                parse_mode=enums.ParseMode.HTML
            )
            
            # Send test message to dump channel
            await client.send_message(
                channel_id,
                f"💾 <b>Dump Channel Activated</b>\n\n"
                f"<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"<b>Set by:</b> {message.from_user.mention}\n\n"
                f"<i>This channel will now store backup copies of all uploaded files.</i>",
                parse_mode=enums.ParseMode.HTML
            )
        else:
            await message.reply("❌ Failed to save dump channel to database.")
    
    except ValueError:
        await message.reply("❌ Invalid channel ID. Please provide a numeric ID.")
    except Exception as e:
        logger.error(f"Error setting dump channel: {e}")
        await message.reply(f"❌ Error: {e}")


@Client.on_message(filters.command("removedumpchannel") & filters.private)
async def remove_dump_channel(client, message):
    """Remove the dump channel"""
    if message.from_user.id != Config.USER_ID:
        await message.reply("❌ This command is owner-only.")
        return
    
    current_dump = await Seishiro.get_config("dump_channel")
    if not current_dump:
        await message.reply("❌ No dump channel is currently set.")
        return
    
    if await Seishiro.set_config("dump_channel", None):
        await message.reply("✅ Dump channel removed successfully.")
    else:
        await message.reply("❌ Failed to remove dump channel.")


@Client.on_message(filters.command("viewchannels") & filters.private)
async def view_channels(client, message):
    """View all configured channels"""
    if message.from_user.id != Config.USER_ID:
        await message.reply("❌ This command is owner-only.")
        return
    
    log_channel = await Seishiro.get_config("log_channel")
    dump_channel = await Seishiro.get_config("dump_channel")
    default_channel = await Seishiro.get_default_channel()
    
    text = "<b>📋 Configured Channels</b>\n\n"
    
    # Log Channel
    if log_channel:
        try:
            chat = await client.get_chat(log_channel)
            text += f"<b>📊 Log Channel:</b>\n"
            text += f"├ <b>Name:</b> {chat.title}\n"
            text += f"└ <b>ID:</b> <code>{log_channel}</code>\n\n"
        except:
            text += f"<b>📊 Log Channel:</b> <code>{log_channel}</code> (⚠️ Cannot access)\n\n"
    else:
        text += "<b>📊 Log Channel:</b> Not set\n\n"
    
    # Dump Channel
    if dump_channel:
        try:
            chat = await client.get_chat(dump_channel)
            text += f"<b>💾 Dump Channel:</b>\n"
            text += f"├ <b>Name:</b> {chat.title}\n"
            text += f"└ <b>ID:</b> <code>{dump_channel}</code>\n\n"
        except:
            text += f"<b>💾 Dump Channel:</b> <code>{dump_channel}</code> (⚠️ Cannot access)\n\n"
    else:
        text += "<b>💾 Dump Channel:</b> Not set\n\n"
    
    # Default Upload Channel
    if default_channel:
        try:
            chat = await client.get_chat(default_channel)
            text += f"<b>⬆️ Default Upload Channel:</b>\n"
            text += f"├ <b>Name:</b> {chat.title}\n"
            text += f"└ <b>ID:</b> <code>{default_channel}</code>\n\n"
        except:
            text += f"<b>⬆️ Default Upload Channel:</b> <code>{default_channel}</code> (⚠️ Cannot access)\n\n"
    else:
        text += "<b>⬆️ Default Upload Channel:</b> Not set\n\n"
    
    text += "<i>Use /setlogchannel, /setdumpchannel to configure</i>"
    
    await message.reply(text, parse_mode=enums.ParseMode.HTML)


# Helper function to log activities
async def log_activity(client, activity_type: str, details: str, user_id: int = None):
    """
    Log bot activities to the log channel
    
    Args:
        client: Pyrogram client
        activity_type: Type of activity (SEARCH, DOWNLOAD, UPLOAD, ERROR, etc.)
        details: Activity details
        user_id: User ID who triggered the activity (optional)
    """
    try:
        log_channel = await Seishiro.get_config("log_channel")
        if not log_channel:
            return
        
        emoji_map = {
            "SEARCH": "🔍",
            "DOWNLOAD": "⬇️",
            "UPLOAD": "⬆️",
            "ERROR": "❌",
            "SUCCESS": "✅",
            "USER": "👤",
            "ADMIN": "👑",
            "BAN": "🚫",
            "UNBAN": "✅",
            "SETTINGS": "⚙️",
            "CHANNEL": "📢"
        }
        
        emoji = emoji_map.get(activity_type, "📝")
        
        log_text = f"{emoji} <b>{activity_type}</b>\n\n"
        log_text += f"<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        if user_id:
            try:
                user = await client.get_users(user_id)
                log_text += f"<b>User:</b> {user.mention} (<code>{user_id}</code>)\n"
            except:
                log_text += f"<b>User ID:</b> <code>{user_id}</code>\n"
        
        log_text += f"\n{details}"
        
        await client.send_message(log_channel, log_text, parse_mode=enums.ParseMode.HTML)
        
    except Exception as e:
        logger.error(f"Failed to log activity: {e}")


# Helper function to send to dump channel
async def send_to_dump(client, file_id: str, caption: str = None, file_type: str = "document"):
    """
    Send a copy of uploaded file to dump channel
    
    Args:
        client: Pyrogram client
        file_id: Telegram file ID
        caption: File caption (optional)
        file_type: Type of file (document, photo, video)
    """
    try:
        dump_channel = await Seishiro.get_config("dump_channel")
        if not dump_channel:
            return None
        
        dump_caption = f"💾 <b>Backup Copy</b>\n\n"
        if caption:
            dump_caption += caption + "\n\n"
        dump_caption += f"<i>Backed up: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>"
        
        if file_type == "document":
            msg = await client.send_document(
                dump_channel,
                file_id,
                caption=dump_caption,
                parse_mode=enums.ParseMode.HTML
            )
        elif file_type == "photo":
            msg = await client.send_photo(
                dump_channel,
                file_id,
                caption=dump_caption,
                parse_mode=enums.ParseMode.HTML
            )
        elif file_type == "video":
            msg = await client.send_video(
                dump_channel,
                file_id,
                caption=dump_caption,
                parse_mode=enums.ParseMode.HTML
            )
        else:
            return None
        
        return msg.id
        
    except Exception as e:
        logger.error(f"Failed to send to dump channel: {e}")
        return None
