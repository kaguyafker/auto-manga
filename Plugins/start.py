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
            f"👋 HELLO (DEPLOY VERIFIED - V4)!\n\n"
            f"<b>Welcome {message.from_user.first_name}</b>\n"
            "The multi-source search is now active.\n\n"
            "Try sending a manga name like <code>one piece</code> or use /search.\n\n"
            "<i>Debug info: Python 3.10 compat active.</i>"
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
        "<b>👮‍♂️ Admin Shortcuts:</b>\n"
        "• <code>/set log <id></code> - Set activity log channel\n"
        "• <code>/set dump <id></code> - Set file backup channel\n"
        "• <code>/rem log | dump</code> - Remove channels\n"
        "• <code>/channels</code> - View active configs\n\n"
        "<b>💡 Problems?</b>\n"
        "If a search fails, try a different source or check the spelling.\n\n"
        "<i>📢 Dev: @koushik_Sama</i>"
    )
    
    buttons = [[InlineKeyboardButton("🔙 back", callback_data="start_menu")]]
    
    await edit_msg_with_pic(callback_query.message, text, InlineKeyboardMarkup(buttons))


@Client.on_message(filters.command("ping"))
async def ping_handler(client, message):
    await message.reply_text("Pong! 🏓 (Start Plugin Active)")

@Client.on_message(filters.command("id"))
async def id_handler(client, message):
    await message.reply_text(f"👤 **Your ID:** `{message.from_user.id}`\n👑 **Owner ID:** `{Config.USER_ID}`")

@Client.on_message(filters.command("version"))
async def version_handler(client, message):
    from datetime import datetime
    await message.reply_text(f"📅 **Bot Version:** 1.2\n🐍 **Environ:** Python 3.10 Compat\n⏰ **Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

@Client.on_message(filters.command("load"))
async def load_debug_handler(client, message):
    if message.from_user.id != Config.USER_ID:
        return
    
    try:
        import traceback
        status = "🔍 **Import Debug:**\n\n"
        
        try:
            from Plugins import search
            status += "✅ `Plugins.search` loaded.\n"
        except Exception:
            status += f"❌ `Plugins.search` failed:\n<code>{traceback.format_exc()[-500:]}</code>\n"
            
        try:
            from Plugins.Sites import allmanga, mangadex, mangakakalot
            status += "✅ Site APIs loaded.\n"
        except Exception:
            status += f"❌ Sites load failed:\n<code>{traceback.format_exc()[-500:]}</code>\n"
            
        await message.reply_text(status, parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        await message.reply_text(f"Critical debug error: {e}")


