


from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import Config
from Database.database import Seishiro
from Database.database import Seishiro
from Plugins.helper import get_styled_text, admin, edit_msg_with_pic

@Client.on_callback_query(filters.regex("^settings_menu$|^settings_menu_1$"))
async def settings_main_menu(client, callback_query):
    try:
        user_id = callback_query.from_user.id
        if user_id != Config.USER_ID and not await Seishiro.is_admin(user_id):
            await callback_query.answer("❌ You are not authorized to use settings.", show_alert=True)
            return

        buttons = [
            [InlineKeyboardButton("Auto Update Channels", callback_data="header_auto_update_channels")],
            
            [
                InlineKeyboardButton("Banner", callback_data="set_banner_btn"),
                InlineKeyboardButton("Caption", callback_data="set_caption_btn")
            ],
            [
                InlineKeyboardButton("Channel Stickers", callback_data="set_channel_stickers_btn"),
                InlineKeyboardButton("Compress", callback_data="set_compress_btn")
            ],
            [
                InlineKeyboardButton("File Name", callback_data="set_format_btn"),
                InlineKeyboardButton("File Type", callback_data="set_file_type_btn")
            ],

            [InlineKeyboardButton("Watermark Settings", callback_data="header_watermark")],

            [
                InlineKeyboardButton("Hyper Link", callback_data="set_hyperlink_btn"),
                InlineKeyboardButton("Merge Size", callback_data="set_merge_size_btn")
            ],
            [
                InlineKeyboardButton("Password", callback_data="set_password_btn"),
                InlineKeyboardButton("Regex", callback_data="set_regex_btn")
            ],
            [
                InlineKeyboardButton("Thumbnail", callback_data="set_thumb_btn"), 
                InlineKeyboardButton("Update Channel", callback_data="set_channel_btn")
            ],

            [
                InlineKeyboardButton("✨ Home ✨", callback_data="start_menu"),
                InlineKeyboardButton("✨ Next ✨ ", callback_data="settings_menu_2")
            ]
        ]
        
        text = (
            "<code>Settings Menu (Page 1/2)</code>\n\n"
            "<code>Select an option below to configure the bot. "
            "All changes are saved instantly to the database.</code>"
        )

        await edit_msg_with_pic(
            message=callback_query.message,
            text=text,
            buttons=InlineKeyboardMarkup(buttons)
        )
    except Exception as e:
        await callback_query.answer("Error opening settings")

@Client.on_callback_query(filters.regex("^settings_menu_2$"))
async def settings_main_menu_2(client, callback_query):
    try:
        buttons = [
            [InlineKeyboardButton("Dump Channel", callback_data="header_dump_channel")],

            [
                InlineKeyboardButton("Update Text", callback_data="set_update_text_btn"),
            ],

            [InlineKeyboardButton("Monitor & Fsub", callback_data="header_new_items")],

            [
                InlineKeyboardButton(f"Monitor: {'✅ ON' if await Seishiro.get_monitoring_status() else '❌ OFF'}", callback_data="toggle_monitor"),
                InlineKeyboardButton("View Progress 📊", callback_data="view_progress")
            ],

            [
                InlineKeyboardButton("Set Interval", callback_data="set_interval_btn"),
                InlineKeyboardButton("Fsub Mode", callback_data="set_fsub_btn")
            ],
            [
                InlineKeyboardButton("Watermark", callback_data="set_watermark_btn"),
                InlineKeyboardButton("Delete Timer", callback_data="set_deltimer_btn")
            ],

            [InlineKeyboardButton("Manga Source", callback_data="header_source")],

            [
                InlineKeyboardButton(f"📡 Source: {await Seishiro.get_config('manga_source', 'mangadex')}", callback_data="set_source_btn")
            ],

            [InlineKeyboardButton("Admin Controls", callback_data="header_admins")],
            
            [
                InlineKeyboardButton("Admins 👮‍♂️", callback_data="admin_menu_btn")
            ],

            [
                InlineKeyboardButton("⬅️ Back ⬅️", callback_data="settings_menu_1"),
                InlineKeyboardButton("❄️ Close ❄️", callback_data="stats_close")
            ]
        ]
        
        dump_ch = await Seishiro.get_config("dump_channel")
        update_ch = await Seishiro.get_default_channel()
        
        text = (
            "<code>⚙️ Settings Menu (Page 2/2)</code>\n\n"
            f"<code>Current Channels:</code>\n"
            f"<code>🗑️ Dump: {dump_ch if dump_ch else 'Not Set'}</code>\n"
            f"<code>📢 Update: {update_ch if update_ch else 'Not Set'}</code>\n\n"
            "<code>Use arrows to navigate between pages.</code>"
        )

        await edit_msg_with_pic(
            message=callback_query.message,
            text=text,
            buttons=InlineKeyboardMarkup(buttons)
        )
    except Exception as e:
        await callback_query.answer("Error opening settings page 2")

@Client.on_callback_query(filters.regex("^header_(?!dump_channel|source|auto_update_channels|auto_upload_channels|new_items)"))
async def header_callback(client, callback_query):
    await callback_query.answer("Values in this section:", show_alert=False)

@Client.on_callback_query(filters.regex("^stats_close$"))
async def close_callback(client, callback_query):
    await callback_query.message.delete()

@Client.on_callback_query(filters.regex("^start_menu$"))
async def start_menu_cb(client, callback_query):
    caption = (
        f"<code>👋 Hello {callback_query.from_user.first_name}!</code>\n\n"
        f"<code>I am an advanced Manga Downloader & Uploader Bot.</code>\n\n"
        f"<code>Click the buttons below to control me!</code>"
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
    await edit_msg_with_pic(callback_query.message, caption, buttons)


@Client.on_callback_query(filters.regex("^set_source_btn$"))
async def set_source_menu(client, callback_query):
    try:
        current = await Seishiro.get_config('manga_source', 'mangadex')
        text = (
            "<code>📡 Select Manga Source</code>\n\n"
            "<code>Choose which source the bot should use for automatic updates and searching.</code>\n\n"
            f"<code>Current: {current}</code>"
        )
        
        buttons = [
            [
                InlineKeyboardButton(f"{'✅ ' if current == 'mangadex' else ''}MangaDex", callback_data="set_source_mangadex"),
                InlineKeyboardButton(f"{'✅ ' if current == 'webcentral' else ''}WebCentral", callback_data="set_source_webcentral")
            ],
            [
                InlineKeyboardButton(f"{'✅ ' if current == 'mangaforest' else ''}MangaForest", callback_data="set_source_mangaforest"),
                InlineKeyboardButton(f"{'✅ ' if current == 'mangakakalot' else ''}Mangakakalot", callback_data="set_source_mangakakalot")
            ],
            [
                InlineKeyboardButton(f"{'✅ ' if current == 'allmanga' else ''}AllManga", callback_data="set_source_allmanga")
            ],
            [
                InlineKeyboardButton("⬅ back", callback_data="settings_menu")
            ]
        ]
        
        await edit_msg_with_pic(
            message=callback_query.message,
            text=text,
            buttons=InlineKeyboardMarkup(buttons)
        )
    except Exception as e:
        await callback_query.answer("Error opening source menu")




@Client.on_callback_query(filters.regex("^set_source_(.+)$"))
async def set_source_callback(client, callback_query):
    new_source = callback_query.matches[0].group(1)
    await Seishiro.set_config('manga_source', new_source)
    await callback_query.answer(f"Source set to: {new_source}", show_alert=True)
    await set_source_menu(client, callback_query)


