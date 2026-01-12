import logging
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from Database.database import Seishiro
from config import Config
from Plugins.helper import edit_msg_with_pic
from Plugins.logs_dump import log_activity

logger = logging.getLogger(__name__)
logger.info("PLUGIN LOAD: start.py loaded successfully")


@Client.on_message(filters.command("let") & filters.private)
async def let_user_handler(client, message):
    if message.from_user.id != Config.USER_ID:
        return
    
    try:
        if len(message.command) < 2:
            await message.reply("Usage: /let {user_id}")
            return
            
        user_id = int(message.command[1])
        if await Seishiro.add_allowed_user(user_id):
            await message.reply(f"✅ User {user_id} has been allowed.")
        else:
            await message.reply("❌ Failed to allow user.")
    except ValueError:
        await message.reply("❌ Invalid User ID.")
    except Exception as e:
        logger.error(f"Let command error: {e}")
        await message.reply(f"❌ Error: {e}")


@Client.on_message(filters.command("start"), group=1)
async def start_msg(client, message):
    try:
        from Plugins.helper import check_fsub
        missing = await check_fsub(client, message.from_user.id)
        if missing:
            buttons = []
            for ch in missing:
                buttons.append([InlineKeyboardButton(f"Join {ch['title']}", url=ch['url'])])
            
            if len(message.command) > 1:
               deep_link = message.command[1]
               buttons.append([InlineKeyboardButton("done ✅", url=f"https://t.me/{client.me.username}?start={deep_link}")])
            else:
               buttons.append([InlineKeyboardButton("done ✅", url=f"https://t.me/{client.me.username}?start=True")])
               
            await message.reply_text(
                "<b>⚠️ you must join our channels to use this bot!</b>\n\n"
                "Please join the channels below and try again.",
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=enums.ParseMode.HTML
            )
            return

        if len(message.command) > 1:
            payload = message.command[1]
            if payload.startswith("dl_"):
                chapter_id = payload.replace("dl_", "")
                
                file_id = await Seishiro.get_chapter_file(chapter_id)
                if file_id:
                     try:
                        await message.reply_document(file_id)
                     except Exception as e:
                        logger.error(f"Failed to send file {file_id}: {e}")
                        await message.reply("❌ error sending file. it might have been deleted.")
                else:
                     await message.reply("❌ file not found or deleted from db.")
                return

        try:
            if await Seishiro.is_user_banned(message.from_user.id):
                await message.reply_text("🚫 **access denied**\n\nyou are banned from using this bot.")
                return
                
            if message.from_user.id != Config.USER_ID and not await Seishiro.is_user_allowed(message.from_user.id):
                await message.reply_text("🚫 **Access Denied**\n\nYou are not authorized to use this bot.\nContact the owner via @koushik_Sama to get access.")
                return

        except Exception as db_e:
            logger.error(f"Database error (Ban/Auth Check): {db_e}")

        try:
            await Seishiro.add_user(client, message)
        except Exception as db_e:
            logger.error(f"Database error (Add User): {db_e}")

        text = (
            f"👋 hello {message.from_user.first_name}!\n\n"
            f"i am an advanced manga downloader & uploader bot. "
            f"i can help you manage and automate your manga channel.\n\n"
            f"🚀 features:\n"
            f"• auto-upload to channel\n"
            f"• custom thumbnails\n"
            f"• watermarking\n\n" 
            f"click the buttons below to control me!"
        )
        
        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(" Settings", callback_data="settings_menu"),
                InlineKeyboardButton(" Help", callback_data="help_menu")
            ],
            [
                InlineKeyboardButton(" Official Channel", url="https://t.me/koushik_Sama"),
                InlineKeyboardButton(" Developer", url="https://t.me/koushik_Sama")
            ]
        ])

        # Log the start activity
        await log_activity(
            client,
            "USER",
            f"👤 <b>Bot Started</b>\n"
            f"<b>Name:</b> {message.from_user.first_name}\n"
            f"<b>Username:</b> @{message.from_user.username if message.from_user.username else 'N/A'}",
            message.from_user.id
        )

        try:
            await message.reply_text(
                text=text,
                reply_markup=buttons,
                parse_mode=enums.ParseMode.HTML,
                disable_web_page_preview=True
            )
        except Exception as img_e:
            logger.error(f"Failed to send menu: {img_e}")

    except Exception as e:
        logger.error(f"/start failed: {e}", exc_info=True)
        try:
            await message.reply_text(f"✅ Bot is alive! (Error displaying menu: {e})")
        except:
            pass




@Client.on_callback_query(filters.regex("^help_menu$"))
async def help_menu(client, callback_query):
    text = (
        "<b>📚 How to Use Automatic Manga Bot</b>\n\n"
        "<b>1️⃣ Search for Manga:</b>\n"
        "Simply type the name of the manga you are looking for in this chat.\n"
        "<i>Example:</i> One Piece or Naruto\n\n"
        "<b>2️⃣ Select a Source:</b>\n"
        "I will show you a list of websites where I found the manga. Click on a button to see results from that site.\n"
        "<i>Supported Sites: MangaDex, MangaKakalot, etc.</i>\n\n"
        "<b>3️⃣ Download Chapters:</b>\n"
        "• <b>Single Chapter:</b> Click on a chapter number to download it immediately.\n"
        "• <b>Custom Range:</b> Click 'Custom Download' to download multiple chapters at once (e.g., 10-50).\n\n"
        "<b>4️⃣ Subscriptions:</b>\n"
        "Currently, subscriptions are managed automatically when you interact with a manga. (Check Settings for more options).\n\n"
        "<b>💡 Problems?</b>\n"
        "If a search fails, try a different source or check the spelling.\n\n"
        "<i>📢 Dev: @koushik_Sama</i>"
    )
    
    buttons = [[InlineKeyboardButton("🔙 back", callback_data="start_menu")]]
    
    await edit_msg_with_pic(callback_query.message, text, InlineKeyboardMarkup(buttons))


