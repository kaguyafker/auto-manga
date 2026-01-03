


from pyrogram import Client, filters, enums
from config import Config
from Database.database import Seishiro
from pyrogram.types import InputMediaPhoto

def admin_filter(filter, client, message):
    return message.from_user.id == Config.USER_ID or message.from_user.id in Seishiro.ADMINS

admin = filters.create(admin_filter)

user_states = {}
user_data = {} # For storing interaction context (e.g. download selections)
WAITING_RENAME_DB = "WAITING_RENAME_DB"
WAITING_THUMBNAIL = "WAITING_THUMBNAIL" 
WAITING_WATERMARK = "WAITING_WATERMARK"
WAITING_CHANNEL_ID = "WAITING_CHANNEL_ID"
WAITING_DUMP_CHANNEL = "WAITING_DUMP_CHANNEL"
WAITING_LOG_CHANNEL = "WAITING_LOG_CHANNEL"
WAITING_CHAPTER_INPUT = "WAITING_CHAPTER_INPUT" # NEW

def get_styled_text(text: str) -> str:
    """
    Apply consistent styling: Monospace.
    """
    return f"<code>{text}</code>"

async def check_ban(user_id):
    return await Seishiro.is_user_banned(user_id)

async def edit_msg_with_pic(message, text, buttons, photo=None):
    """
    Edits the message. 
    If photo is provided, sends/edits with photo.
    If no photo, ensures message is text-only (deletes old if it was media).
    """
    try:
        if photo:
            if message.photo:
                await message.edit_media(
                    media=InputMediaPhoto(media=photo, caption=text),
                    reply_markup=buttons
                )
            else:
                await message.delete()
                await message.reply_photo(
                    photo=photo,
                    caption=text,
                    reply_markup=buttons,
                    parse_mode=enums.ParseMode.HTML
                )
        else:
            # We want text only
            if message.photo or message.video or message.document:
                await message.delete()
                await message.reply_text(
                    text=text,
                    reply_markup=buttons,
                    parse_mode=enums.ParseMode.HTML
                )
            else:
                await message.edit_text(
                    text=text,
                    reply_markup=buttons,
                    parse_mode=enums.ParseMode.HTML
                )
    except Exception as e:
        # Fallback if something goes wrong (e.g. message deleted)
        try:
             await message.reply_text(text, reply_markup=buttons, parse_mode=enums.ParseMode.HTML)
        except:
             pass

async def check_fsub(client, user_id):
    """
    Checks if user is joined in all FSub channels.
    Returns a list of dicts: {'title': str, 'url': str} for missing channels.
    """
    try:
        fsub_channels = await Seishiro.get_fsub_channels()
        if not fsub_channels:
            return []

        missing = []
        for cid in fsub_channels:
            mode = await Seishiro.get_channel_mode(cid)
            if mode != "on":
                continue

            try:
                await client.get_chat_member(cid, user_id)
            except Exception: # Not a member
                try:
                    chat = await client.get_chat(cid)
                    if chat.username:
                        link = f"https://t.me/{chat.username}"
                    else:
                        invite = await client.create_chat_invite_link(cid, member_limit=1)
                        link = invite.invite_link
                    
                    missing.append({'title': chat.title, 'url': link})
                except Exception as e:
                    print(f"FSub Error for {cid}: {e}")
                    continue
        
        return missing

    except Exception as e:
        print(f"Check FSub Failed: {e}")
        return []


