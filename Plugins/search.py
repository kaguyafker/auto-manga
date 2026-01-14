
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import Config
from Plugins.downloading import Downloader
from Plugins.Sites.mangadex import MangaDexAPI
from Plugins.Sites.mangaforest import MangaForestAPI
from Database.database import Seishiro
from Plugins.helper import edit_msg_with_pic, get_styled_text, user_states, user_data, WAITING_CHAPTER_INPUT
from Plugins.logs_dump import log_activity, send_to_dump
import logging
import asyncio
import shutil
from pathlib import Path
import os
import re

logger = logging.getLogger(__name__)

from Plugins.Sites.mangakakalot import MangakakalotAPI
from Plugins.Sites.allmanga import AllMangaAPI

SITES = {
    "MangaDex": MangaDexAPI,
    "MangaForest": MangaForestAPI,
    "Mangakakalot": MangakakalotAPI,
    "AllManga": AllMangaAPI,
    "WebCentral": None # Placeholder until verified or imported
}

try:
    from Plugins.Sites.webcentral import WebCentralAPI
    SITES["WebCentral"] = WebCentralAPI
except ImportError:
    pass

def get_api_class(source):
    return SITES.get(source)


async def search_single_source(source: str, query: str):
    """
    Search a single source and return results, or empty list on error.
    Returns: List of manga dictionaries or empty list
    """
    try:
        API = get_api_class(source)
        if not API:
            logger.warning(f"Source {source} has no API class")
            return []
        
        async with API(Config) as api:
            if not hasattr(api, 'search_manga'):
                logger.warning(f"Source {source} does not implement search_manga")
                return []
            
            results = await api.search_manga(query)
            return results if results else []
    except Exception as e:
        logger.error(f"Search failed for {source}: {e}")
        return []


@Client.on_message(filters.text & filters.private & ~filters.command(["start", "help", "settings", "search"]))
async def message_handler(client, message):
    try:
        user_id = message.from_user.id
        logger.info(f"Search message handler triggered for {user_id}: {message.text}")
        if user_id == Config.USER_ID:
             await message.reply(f"🔍 Debug: Message Handler Triggered: {message.text}")
        
        state_info = user_states.get(user_id)
        if isinstance(state_info, dict) and state_info.get("state") == WAITING_CHAPTER_INPUT:
            await custom_dl_input_handler(client, message)
            return
        elif user_id in user_states:
            message.continue_propagation()
            return
        
        # Check authorization before search
        from Plugins.helper import check_fsub
        
        # Check force subscribe
        missing = await check_fsub(client, user_id)
        if missing:
            from pyrogram.types import InlineKeyboardButton
            buttons = []
            for ch in missing:
                buttons.append([InlineKeyboardButton(f"Join {ch['title']}", url=ch['url'])])
            buttons.append([InlineKeyboardButton("✅ Done", url=f"https://t.me/{client.me.username}?start=True")])
            
            await message.reply_text(
                "<b>⚠️ You must join our channels to use this bot!</b>\n\n"
                "Please join the channels below and try again.",
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=enums.ParseMode.HTML
            )
            return
        
        # Check if user is banned
        if await Seishiro.is_user_banned(user_id):
            await message.reply_text("🚫 **Access Denied**\n\nYou are banned from using this bot.")
            return
        
        # Check if user is allowed
        if user_id != Config.USER_ID and not await Seishiro.is_user_allowed(user_id):
            await message.reply_text("🚫 **Access Denied**\n\nYou are not authorized to use this bot.\nContact the owner via @koushik_Sama to get access.")
            return
        
        # Text Search Implementation
        await search_logic(client, message, message.text.strip())
    except Exception as e:
        logger.error(f"Error in search message_handler: {e}")
        await message.reply(f"❌ search error: {e}")

@Client.on_message(filters.command("search") & filters.private)
async def search_command_handler(client, message):
    try:
        user_id = message.from_user.id
        logger.info(f"Search command handler triggered for {user_id}: {message.text}")
        if user_id == Config.USER_ID:
             await message.reply(f"🔍 Debug: Command Handler Triggered")
        
        # Check authorization before search
        from Plugins.helper import check_fsub
        
        # Check force subscribe
        missing = await check_fsub(client, user_id)
        if missing:
            from pyrogram.types import InlineKeyboardButton
            buttons = []
            for ch in missing:
                buttons.append([InlineKeyboardButton(f"Join {ch['title']}", url=ch['url'])])
            buttons.append([InlineKeyboardButton("✅ Done", url=f"https://t.me/{client.me.username}?start=True")])
            
            await message.reply_text(
                "<b>⚠️ You must join our channels to use this bot!</b>\n\n"
                "Please join the channels below and try again.",
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=enums.ParseMode.HTML
            )
            return
        
        # Check if user is banned
        if await Seishiro.is_user_banned(user_id):
            await message.reply_text("🚫 **Access Denied**\n\nYou are banned from using this bot.")
            return
        
        # Check if user is allowed
        if user_id != Config.USER_ID and not await Seishiro.is_user_allowed(user_id):
            await message.reply_text("🚫 **Access Denied**\n\nYou are not authorized to use this bot.\nContact the owner via @koushik_Sama to get access.")
            return
        
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            await message.reply("❌ usage: /search <query>")
            return
        
        query = parts[1].strip()
        await search_logic(client, message, query)
    except Exception as e:
        logger.error(f"Error in search_command_handler: {e}")
        await message.reply(f"❌ search error: {e}")

async def search_logic(client, message, query):
    """
    Search all sources concurrently and display results grouped by source.
    """
    if len(query) < 2:
        await message.reply("❌ Query too short. Please enter at least 2 characters.")
        return
    
    # Show searching status
    status_msg = await message.reply(
        f"<b>🔍 Searching all sources for:</b> {query}\n\n<i>⏳ Please wait...</i>",
        parse_mode=enums.ParseMode.HTML
    )
    
    try:
        # Get all available sources
        available_sites = [s for s in SITES.keys() if SITES[s] is not None]
        
        if not available_sites:
            await status_msg.edit_text("❌ No sources available.")
            return
        
        # Search all sources concurrently
        logger.info(f"Searching {len(available_sites)} sources for: {query}")
        search_tasks = [search_single_source(source, query) for source in available_sites]
        results_by_source = await asyncio.gather(*search_tasks, return_exceptions=True)
        
        # Build inline buttons from results
        buttons = []
        total_results = 0
        results_summary = {}
        
        for source, results in zip(available_sites, results_by_source):
            if isinstance(results, Exception):
                logger.error(f"Exception from {source}: {results}")
                results_summary[source] = 0
                continue
            
            if not results or len(results) == 0:
                results_summary[source] = 0
                continue
            
            # Take top 5 results per source
            source_results = results[:5]
            results_summary[source] = len(source_results)
            
            for manga in source_results:
                # Truncate title to fit in button (max 64 bytes for callback_data)
                title = manga['title'][:35].strip()
                if len(manga['title']) > 35:
                    title += "..."
                
                button_text = f"{source}: {title}"
                
                # Ensure manga_id is safe for callback data
                manga_id = str(manga['id'])[:20]  # Limit ID length
                
                buttons.append([InlineKeyboardButton(
                    button_text,
                    callback_data=f"view_{source}_{manga_id}"
                )])
                total_results += 1
        
        # Add close button
        buttons.append([InlineKeyboardButton("❌ Close", callback_data="stats_close")])
        
        # Display results
        if total_results == 0:
            summary_text = "\n".join([f"• {s}: 0 results" for s in available_sites])
            await status_msg.edit_text(
                f"<b>❌ No results found for:</b> {query}\n\n{summary_text}",
                parse_mode=enums.ParseMode.HTML
            )
        else:
            summary_text = "\n".join([
                f"• {s}: {results_summary.get(s, 0)} result(s)" 
                for s in available_sites if results_summary.get(s, 0) > 0
            ])
            await status_msg.edit_text(
                f"<b>✅ Found {total_results} results for:</b> {query}\n\n{summary_text}\n\n<i>Select a manga to view chapters:</i>",
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=enums.ParseMode.HTML
            )
        
        # Log the search activity
        await log_activity(
            client,
            "SEARCH",
            f"<b>Query:</b> {query}\n<b>Total Results:</b> {total_results}\n<b>Sources Searched:</b> {len(available_sites)}",
            message.from_user.id
        )
        
    except Exception as e:
        logger.error(f"Error in search_logic: {e}", exc_info=True)
        await status_msg.edit_text(f"❌ Search error: {e}")


# Removed search_source_cb - no longer needed as we search all sources simultaneously


@Client.on_callback_query(filters.regex("^view_"))
async def view_manga_cb(client, callback_query):
    parts = callback_query.data.split("_", 2)
    source = parts[1]
    manga_id = parts[2]
    
    api = get_api_class(source)
    if not api: return

    async with api(Config) as api:
        info = await api.get_manga_info(manga_id)
    
    if not info:
        await callback_query.answer("error fetching details", show_alert=True)
        return

    caption = (
        f"<b>📖 {info['title']}</b>\n"
        f"<b>Source:</b> {source}\n"
        f"<b>ID:</b> {manga_id}\n\n"
        f"Select an option:"
    )
    
    buttons = [
        [InlineKeyboardButton("⬇ download chapters", callback_data=f"chapters_{source}_{manga_id}_0")],
        [InlineKeyboardButton("⬇ custom download (range)", callback_data=f"custom_dl_{source}_{manga_id}")],
        [InlineKeyboardButton("❌ close", callback_data="stats_close")] 
    ]
    
    msg = callback_query.message
    await edit_msg_with_pic(msg, caption, InlineKeyboardMarkup(buttons))



@Client.on_callback_query(filters.regex("^chapters_"))
async def chapters_list_cb(client, callback_query):
    parts = callback_query.data.split("_")
    if len(parts) < 4:
        await callback_query.answer("❌ Invalid callback data", show_alert=True)
        return
    
    source = parts[1]
    offset = int(parts[-1])  # Last part is always offset
    manga_id = "_".join(parts[2:-1])  # Everything between source and offset
    
    API = get_api_class(source)
    async with API(Config) as api:
        chapters = await api.get_manga_chapters(manga_id, limit=10, offset=offset)
    
    if not chapters and offset == 0:
        await callback_query.answer("No chapters found.", show_alert=True)
        return
    elif not chapters:
        await callback_query.answer("No more chapters.", show_alert=True)
        return

    buttons = []
    row = []
    for ch in chapters:
        ch_num = ch['chapter']
        btn_text = f"ch {ch_num}"
        
        
        row.append(InlineKeyboardButton(btn_text, callback_data=f"dl_ask_{source}_{manga_id}_{ch['id'][:20]}")) # DANGEROUS HACK
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row: buttons.append(row)
    
    nav = []
    if offset >= 10:
        nav.append(InlineKeyboardButton("⬅ prev", callback_data=f"chapters_{source}_{manga_id}_{offset-10}"))
    nav.append(InlineKeyboardButton("next ➡", callback_data=f"chapters_{source}_{manga_id}_{offset+10}"))
    buttons.append(nav)
    
    buttons.append([InlineKeyboardButton("⬅ back to manga", callback_data=f"view_{source}_{manga_id}")])
    
    caption_text = f"<b>select chapter to download (standard):</b>\n<b>Source:</b> {source}\npage: {int(offset/10)+1}\n<i>note: uploads to default channel.</i>"
    
    try:
        if callback_query.message.photo:
            await callback_query.message.edit_caption(caption=caption_text, reply_markup=InlineKeyboardMarkup(buttons))
        else:
            await callback_query.message.edit_text(caption_text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        print(f"Edit error: {e}")





@Client.on_callback_query(filters.regex("^custom_dl_"))
async def custom_dl_start_cb(client, callback_query):
    parts = callback_query.data.split("_")
    source = parts[2]
    manga_id = "_".join(parts[3:])
    
    user_id = callback_query.from_user.id
    
    user_states[user_id] = {"state": WAITING_CHAPTER_INPUT}
    user_data[user_id] = {
        'source': source,
        'manga_id': manga_id
    }
    
    await callback_query.message.reply_text(
        "<b>⬇ custom download mode</b>\n\n"
        "Please enter the Chapter Number you want to download.\n"
        "You can download a single chapter or a range.\n\n"
        "<b>Examples:</b>\n"
        "5 (Download Chapter 5)\n"
        "10-20 (Download Chapters 10 to 20)\n\n"
        "<i>Downloads will be sent to your Private Chat.</i>",
        parse_mode=enums.ParseMode.HTML
    )
    await callback_query.answer()

async def custom_dl_input_handler(client, message):
    user_id = message.from_user.id
    text = message.text.strip()
    
    if user_id in user_states:
        del user_states[user_id]
        
    data = user_data.get(user_id)
    if not data:
        await message.reply("❌ session expired. please search again.")
        return
        
    source = data['source']
    manga_id = data['manga_id']
    
    target_chapters = [] # List of floats/strings numbers
    is_range = False
    
    try:
        if "-" in text:
            is_range = True
            start, end = map(float, text.split("-"))
            range_min = min(start, end)
            range_max = max(start, end)
        else:
            target_chapters.append(float(text))
    except ValueError:
        await message.reply("❌ invalid format. please enter numbers like `5` or `10-20`.")
        return

    status_msg = await message.reply("<i>⏳ fetching chapter list...</i>", parse_mode=enums.ParseMode.HTML)
    
    API = get_api_class(source)
    all_chapters = []
    
    
    async with API(Config) as api:
        offset = 0
        while True:
            batch = await api.get_manga_chapters(manga_id, limit=100, offset=offset)
            if not batch: break
            all_chapters.extend(batch)
            if len(batch) < 100: break
            offset += 100
            if len(all_chapters) > 2000: break # Safety Break
            
    if not all_chapters:
        await status_msg.edit_text("❌ no chapters found.")
        return

    to_download = []
    for ch in all_chapters:
        try:
            ch_num = float(ch['chapter'])
            if is_range:
                if range_min <= ch_num <= range_max:
                    to_download.append(ch)
            else:
                if ch_num in target_chapters:
                     to_download.append(ch)
        except:
             pass # Skip non-numeric chapters
             
    if not to_download:
        await status_msg.edit_text(f"❌ no chapters found for input: {text}")
        return

    await status_msg.edit_text(f"✅ Found {len(to_download)} chapters. Starting download...")
    
    to_download.sort(key=lambda x: float(x['chapter']))
    
    for ch in to_download:
        await execute_download(client, message.chat.id, source, manga_id, ch['id'], user_id) ## Use user_id as upload target?


async def execute_download(client, target_chat_id, source, manga_id, chapter_id, status_chat_id=None):
    """
    Downloads and uploads a chapter.
    status_chat_id: Where to send updates (if different from target).
    """
    if not status_chat_id: status_chat_id = target_chat_id
    
    status_msg = await client.send_message(status_chat_id, "<i>⏳ Initializing download...</i>", parse_mode=enums.ParseMode.HTML)
    
    try:
        API = get_api_class(source)
        async with API(Config) as api:
            meta = await api.get_chapter_info(chapter_id)
            if not meta:
                await status_msg.edit_text("❌ failed to get chapter info.")
                return
            
            if meta.get('manga_title') in ['Unknown', None]:
                 m_info = await api.get_manga_info(manga_id)
                 if m_info: meta['manga_title'] = m_info['title']

            images = await api.get_chapter_images(chapter_id)
            
        if not images:
            await status_msg.edit_text(f"❌ no images in chapter {meta.get('chapter', '?')}")
            return
            
        chapter_dir = Path(Config.DOWNLOAD_DIR) / f"{source}_{manga_id}" / f"ch_{meta['chapter']}"
        chapter_dir.mkdir(parents=True, exist_ok=True)
        
        await status_msg.edit_text(f"<i>⬇ downloading {len(images)} pages...</i>", parse_mode=enums.ParseMode.HTML)
        
        async with Downloader(Config) as downloader:
            if not await downloader.download_images(images, chapter_dir):
                 await status_msg.edit_text("❌ download failed.")
                 return
            
            await status_msg.edit_text("<i>⚙️ processing pdf...</i>", parse_mode=enums.ParseMode.HTML)
            
            file_type = await Seishiro.get_config("file_type", "pdf")
            quality = await Seishiro.get_config("image_quality")
            
            banner_1 = await Seishiro.get_config("banner_image_1")
            banner_2 = await Seishiro.get_config("banner_image_2")
            
            intro_p = None; outro_p = None
            if banner_1:
                 intro_p = chapter_dir.parent / "intro.jpg"
                 try: await client.download_media(banner_1, file_name=str(intro_p))
                 except: intro_p = None
            if banner_2:
                 outro_p = chapter_dir.parent / "outro.jpg"
                 try: await client.download_media(banner_2, file_name=str(outro_p))
                 except: outro_p = None

            final_path = await asyncio.to_thread(
                 downloader.create_chapter_file,
                 chapter_dir, meta['manga_title'], meta['chapter'], meta['title'],
                 file_type, intro_p, outro_p, quality
            )
            
            if intro_p and intro_p.exists(): intro_p.unlink()
            if outro_p and outro_p.exists(): outro_p.unlink()
            
            if not final_path:
                 await status_msg.edit_text("❌ failed to create file.")
                 return
            
            await status_msg.edit_text(f"<i>⬆ uploading...</i>", parse_mode=enums.ParseMode.HTML)
            caption = f"<b>{meta['manga_title']} - Ch {meta['chapter']}</b>"
            
            # Upload to target channel
            uploaded_msg = await client.send_document(
                chat_id=target_chat_id,
                document=final_path,
                caption=caption,
                parse_mode=enums.ParseMode.HTML
            )
            
            # Log the upload activity
            await log_activity(
                client,
                "UPLOAD",
                f"<b>Manga:</b> {meta['manga_title']}\n"
                f"<b>Chapter:</b> {meta['chapter']}\n"
                f"<b>Source:</b> {source}\n"
                f"<b>Pages:</b> {len(images)}\n"
                f"<b>File Type:</b> {file_type}\n"
                f"<b>Target Channel:</b> <code>{target_chat_id}</code>",
                status_chat_id if status_chat_id != target_chat_id else None
            )
            
            # Send to dump channel for backup
            await send_to_dump(
                client,
                uploaded_msg.document.file_id,
                caption,
                "document"
            )
            
            shutil.rmtree(chapter_dir, ignore_errors=True)
            if final_path.exists(): final_path.unlink()
            
            await status_msg.delete() # Cleanup status Message on success to avoid clutter? 

    except Exception as e:
        logger.error(f"DL Error: {e}", exc_info=True)
        await status_msg.edit_text(f"❌ Error: {e}")


@Client.on_callback_query(filters.regex("^dl_ask_"))
async def dl_ask_cb(client, callback_query):
    data = callback_query.data.split("_")
    source = data[2]
    manga_id = data[3]
    chapter_id = "_".join(data[4:])
    
    
    db_channel = await Seishiro.get_default_channel()
    channel_id = int(db_channel) if db_channel else Config.CHANNEL_ID
    
    await callback_query.answer("Starting download...", show_alert=False)
    await execute_download(client, channel_id, source, manga_id, chapter_id, callback_query.message.chat.id)



