


from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from Database.database import Seishiro
from Plugins.helper import get_styled_text, user_states, edit_msg_with_pic
from Plugins.Settings.input_helper import timeout_handler
from Plugins.Settings.main_settings import settings_main_menu_2
import asyncio
from config import Config


@Client.on_callback_query(filters.regex("^admin_menu_btn$"))
async def admin_menu_cb(client, callback_query):
    if callback_query.from_user.id != Config.USER_ID and not await Seishiro.is_admin(callback_query.from_user.id):
        await callback_query.answer("❌ Admin Only area!", show_alert=True)
        return

    text = get_styled_text(
        "👮‍♂️ Admin Controls\n\n"
        "Manage bot administrators and other restricted settings."
    )
    
    buttons = [
        [
            InlineKeyboardButton("add admin ➕", callback_data="admin_add_btn"),
            InlineKeyboardButton("del admin ➖", callback_data="admin_del_btn")
        ],
        [
            InlineKeyboardButton("ban user ", callback_data="admin_ban_btn"),
            InlineKeyboardButton("unban user ", callback_data="admin_unban_btn")
        ],
        [
            InlineKeyboardButton("list admins ", callback_data="admin_list_btn"),
            InlineKeyboardButton("allowed users 👥", callback_data="admin_allowed_list_btn")
        ],
        [
            InlineKeyboardButton("view watermark ", callback_data="admin_view_wm_btn")
        ],
         [
            InlineKeyboardButton("add fsub ➕", callback_data="add_fsub_btn"),
            InlineKeyboardButton("rem fsub ➖", callback_data="rem_fsub_btn"),
            InlineKeyboardButton("fsub Config 📢", callback_data="fsub_config_btn")
        ],
        [
            InlineKeyboardButton("broadcast ", callback_data="broadcast_btn"),
            InlineKeyboardButton("channels ", callback_data="admin_channels_btn")
        ],
        [
            InlineKeyboardButton("⬅ back", callback_data="settings_menu_2")
        ]
    ]
    
    await edit_msg_with_pic(
        message=callback_query.message,
        text=text,
        buttons=InlineKeyboardMarkup(buttons)
    )


@Client.on_callback_query(filters.regex("^admin_add_btn$"))
async def add_admin_btn_cb(client, callback_query):
    text = get_styled_text(
        "➕ Add Admin\n\n"
        "Send the User ID of the new admin.\n"
        "(Auto-close in 30s)"
    )
    user_states[callback_query.from_user.id] = {"state": "waiting_add_admin"}
    buttons = [[InlineKeyboardButton("❌ cancel", callback_data="cancel_input")]]
    await edit_msg_with_pic(callback_query.message, text, InlineKeyboardMarkup(buttons))
    asyncio.create_task(timeout_handler(client, callback_query.message, callback_query.from_user.id, "waiting_add_admin"))

@Client.on_callback_query(filters.regex("^admin_del_btn$"))
async def del_admin_btn_cb(client, callback_query):
    text = get_styled_text(
        "➖ Remove Admin\n\n"
        "Send the User ID to remove.\n"
        "(Auto-close in 30s)"
    )
    user_states[callback_query.from_user.id] = {"state": "waiting_del_admin"}
    buttons = [[InlineKeyboardButton("❌ cancel", callback_data="cancel_input")]]
    await edit_msg_with_pic(callback_query.message, text, InlineKeyboardMarkup(buttons))
    asyncio.create_task(timeout_handler(client, callback_query.message, callback_query.from_user.id, "waiting_del_admin"))

@Client.on_callback_query(filters.regex("^admin_ban_btn$"))
async def ban_user_btn_cb(client, callback_query):
    text = get_styled_text(
        "🚫 Ban User\n\n"
        "Send the User ID to ban.\n"
        "(Auto-close in 30s)"
    )
    user_states[callback_query.from_user.id] = {"state": "waiting_ban_id"}
    buttons = [[InlineKeyboardButton("❌ cancel", callback_data="cancel_input")]]
    await edit_msg_with_pic(callback_query.message, text, InlineKeyboardMarkup(buttons))
    asyncio.create_task(timeout_handler(client, callback_query.message, callback_query.from_user.id, "waiting_ban_id"))

@Client.on_callback_query(filters.regex("^admin_unban_btn$"))
async def unban_user_btn_cb(client, callback_query):
    text = get_styled_text(
        "✅ Unban User\n\n"
        "Send the User ID to unban.\n"
        "(Auto-close in 30s)"
    )
    user_states[callback_query.from_user.id] = {"state": "waiting_unban_id"}
    buttons = [[InlineKeyboardButton("❌ cancel", callback_data="cancel_input")]]
    await edit_msg_with_pic(callback_query.message, text, InlineKeyboardMarkup(buttons))
    asyncio.create_task(timeout_handler(client, callback_query.message, callback_query.from_user.id, "waiting_unban_id"))

@Client.on_callback_query(filters.regex("^admin_list_btn$"))
async def list_admins_cb(client, callback_query):
    try:
        admins = await Seishiro.get_admins()
        list_text = f"👮‍♂️ admin list:\n\n"
        
        try:
             owner = await client.get_users(Config.user_id)
             owner_name = owner.first_name
        except:
             owner_name = "owner"
        list_text += f"• {owner_name} (`{Config.USER_ID}`) (Owner)\n"

        for uid in admins:
            try:
                user = await client.get_users(uid)
                name = user.first_name
            except:
                name = "Unknown"
            list_text += f"• {name} (`{uid}`)\n"
        
        buttons = [[InlineKeyboardButton("⬅ back", callback_data="admin_menu_btn")]]
        await edit_msg_with_pic(callback_query.message, get_styled_text(list_text), InlineKeyboardMarkup(buttons))
    except Exception as e:
        await callback_query.answer(f"Error: {e}", show_alert=True)



        
@Client.on_callback_query(filters.regex("^fsub_config_btn$"))
async def fsub_config_menu(client, callback_query):
    channels = await Seishiro.get_fsub_channels()
    buttons = []
    for cid in channels:
        try:
            chat = await client.get_chat(cid)
            mode = await Seishiro.get_channel_mode(cid)
            status = "🟢" if mode == "on" else "🔴"
            buttons.append([InlineKeyboardButton(f"{status} {chat.title}", callback_data=f"rfs_ch_{cid}")])
        except Exception:
             buttons.append([InlineKeyboardButton(f"Invalid {cid}", callback_data=f"rfs_ch_{cid}")])
    
    if not buttons:
        buttons.append([InlineKeyboardButton("no channels found", callback_data="no_channels")])
        
    buttons.append([InlineKeyboardButton("⬅ back", callback_data="admin_menu_btn")])
        
    await edit_msg_with_pic(callback_query.message, get_styled_text("📢 FSub Configuration\nTap to toggle Mode."), InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^admin_view_wm_btn$"))
async def view_wm_cb(client, callback_query):
    try:
        current_wm = await Seishiro.get_watermark()
        if current_wm:
            text = (
                f"💧 Current Watermark:\n\n"
                f"Text: {current_wm['text']}\n"
                f"Pos: {current_wm['position']}\n"
                f"Col: {current_wm['color']} | Op: {current_wm['opacity']}\n"
                f"Size: {current_wm['font_size']}"
            )
        else:
            text = "💧 watermark: not set"
            
        buttons = [[InlineKeyboardButton("⬅ back", callback_data="admin_menu_btn")]]
        await edit_msg_with_pic(callback_query.message, get_styled_text(text), InlineKeyboardMarkup(buttons))
    except Exception as e:
        await callback_query.answer(f"Error: {e}", show_alert=True)

@Client.on_callback_query(filters.regex("^add_fsub_btn$"))
async def add_fsub_btn_cb(client, callback_query):
    text = get_styled_text(
        "➕ Add Force-Sub Channel\n\n"
        "Send the Channel ID (bot must be admin there).\n"
        "(Auto-close in 30s)"
    )
    user_states[callback_query.from_user.id] = {"state": "waiting_fsub_id"} # Reuse existing state
    buttons = [[InlineKeyboardButton("❌ cancel", callback_data="cancel_input")]]
    await edit_msg_with_pic(callback_query.message, text, InlineKeyboardMarkup(buttons))
    asyncio.create_task(timeout_handler(client, callback_query.message, callback_query.from_user.id, "waiting_fsub_id"))

@Client.on_callback_query(filters.regex("^rem_fsub_btn$"))
async def rem_fsub_btn_cb(client, callback_query):
    text = get_styled_text(
        "➖ Remove Force-Sub Channel\n\n"
        "Send the Channel ID to remove.\n"
        "(Auto-close in 30s)"
    )
    user_states[callback_query.from_user.id] = {"state": "waiting_fsub_rem_id"} # Reuse existing state
    buttons = [[InlineKeyboardButton("❌ cancel", callback_data="cancel_input")]]
    await edit_msg_with_pic(callback_query.message, text, InlineKeyboardMarkup(buttons))
    asyncio.create_task(timeout_handler(client, callback_query.message, callback_query.from_user.id, "waiting_fsub_rem_id"))

@Client.on_callback_query(filters.regex("^broadcast_btn$"))
async def broadcast_btn_cb(client, callback_query):
    text = get_styled_text(
        "📢 Broadcast Message\n\n"
        "Send the Message you want to broadcast to all users.\n"
        "(Text, Photo, Video, Sticker, etc.)\n"
        "(Auto-close in 30s)"
    )
    user_states[callback_query.from_user.id] = {"state": "waiting_broadcast_msg"}
    buttons = [[InlineKeyboardButton("❌ cancel", callback_data="cancel_input")]]
    await edit_msg_with_pic(callback_query.message, text, InlineKeyboardMarkup(buttons))
    asyncio.create_task(timeout_handler(client, callback_query.message, callback_query.from_user.id, "waiting_broadcast_msg"))

@Client.on_callback_query(filters.regex("^admin_channels_btn$"))
async def admin_channels_cb(client, callback_query):
    try:
        dump_id = await Seishiro.get_config("dump_channel")
        update_id = await Seishiro.get_default_channel()
        auto_chs = await Seishiro.get_auto_update_channels()

        async def get_name(cid):
            if not cid: return "Not Set"
            try:
                chat = await client.get_chat(int(cid))
                return f"{chat.title} (`{cid}`)"
            except:
                return f"Unknown (`{cid}`)"

        dump_str = await get_name(dump_id)
        update_str = await get_name(update_id)
        
        auto_text = ""
        if auto_chs:
            for c in auto_chs:
                db_title = c.get('title', 'Unknown')
                cid = c.get('_id')
                auto_text += f"\n• {db_title} (`{cid}`)"
        else:
            auto_text = "\n• None"

        text = get_styled_text(
            f"📺 Channel Configuration\n\n"
            f"🗑️ Dump Channel:\n➥ {dump_str}\n\n"
            f"📢 Update Channel:\n➥ {update_str}\n\n"
            f"🤖 Auto-Update Channels:{auto_text}"
        )
        
        buttons = [[InlineKeyboardButton("⬅ back", callback_data="admin_menu_btn")]]
        await edit_msg_with_pic(callback_query.message, text, InlineKeyboardMarkup(buttons))
    except Exception as e:
        await callback_query.answer(f"Error: {e}", show_alert=True)




@Client.on_callback_query(filters.regex("^admin_allowed_list_btn$"))
async def allowed_list_cb(client, callback_query):
    users = await Seishiro.get_allowed_users()
    
    buttons = []
    
    for uid in users:
        try:
            # Try to get user info if possible
            try:
                user = await client.get_chat(uid)
                name = user.first_name or user.title
            except:
                name = "User"
            
            buttons.append([
                InlineKeyboardButton(f"{name} ({uid})", callback_data="ignore"),
                InlineKeyboardButton("❌ Remove", callback_data=f"rem_allow_{uid}")
            ])
        except Exception:
             pass
        
    if not users:
        buttons.append([InlineKeyboardButton("No allowed users found", callback_data="ignore")])
        
    buttons.append([InlineKeyboardButton("⬅ back", callback_data="admin_menu_btn")])
    
    await edit_msg_with_pic(
        callback_query.message, 
        get_styled_text("👥 Allowed Users List\n\nUsers who have access to the bot."),
        InlineKeyboardMarkup(buttons)
    )

@Client.on_callback_query(filters.regex("^rem_allow_"))
async def remove_allowed_cb(client, callback_query):
    try:
        uid = int(callback_query.data.split("_")[-1])
        if await Seishiro.remove_allowed_user(uid):
            await callback_query.answer(f"✅ Removed user {uid}", show_alert=True)
            # Refresh list
            await allowed_list_cb(client, callback_query)
        else:
             await callback_query.answer("❌ Failed to remove user", show_alert=True)
    except Exception as e:
         await callback_query.answer(f"Error: {e}", show_alert=True)
