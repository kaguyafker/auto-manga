


from pyrogram import Client, filters, enums
from Database.database import Seishiro
from Plugins.helper import user_states, get_styled_text
from config import Config
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from Plugins.logs_dump import log_activity


@Client.on_callback_query(filters.regex("^cancel_input$"))
async def cancel_input_cb(client, callback_query):
    user_id = callback_query.from_user.id
    if user_id in user_states:
        del user_states[user_id]
    await callback_query.message.edit_text(
        get_styled_text("❌ Input Cancelled."),
        parse_mode=enums.ParseMode.HTML
    )
    buttons = [[InlineKeyboardButton("🔙 back to settings", callback_data="settings_menu")]]
    await callback_query.message.reply_text("cancelled.", reply_markup=InlineKeyboardMarkup(buttons))


@Client.on_message(filters.private & ~filters.command(["start", "help", "admin"]))
async def settings_input_listener(client, message):
    user_id = message.from_user.id
    if user_id not in user_states:
        return

    state_info = user_states[user_id]
    if not isinstance(state_info, dict):
        return
        
    state = state_info.get("state")
    if state == "WAITING_CHAPTER_INPUT":
        return
    
    handled = False
    try:
        if state == "waiting_caption":
            handled = True
            await Seishiro.set_caption(message.text)
            await message.reply(get_styled_text("✅ Caption Updated Successfully!"), parse_mode=enums.ParseMode.HTML)
            await log_activity(client, "SETTINGS", f"📝 <b>Caption Updated</b>\n<code>{message.text}</code>", user_id)
            
            from Plugins.Settings.media_settings import set_caption_cb
            curr = await Seishiro.get_caption()
            curr_disp = "Set" if curr else "None"
            text = get_styled_text(
                "<b>Caption</b>\n\n"
                "<b>Format:</b>\n"
                "➥ {manga_title}: Manga Name\n"
                "➥ {chapter_num}: Chapter Number\n"
                "➥ {file_name}: File Name\n\n"
                f"➥ Your Value: {curr_disp}"
            )
            buttons = [
                [
                    InlineKeyboardButton("set / change", callback_data="set_caption_input"),
                    InlineKeyboardButton("delete", callback_data="del_caption_btn")
                ],
                [
                    InlineKeyboardButton("⬅ back", callback_data="settings_menu"),
                    InlineKeyboardButton("❄ close ❄", callback_data="stats_close")
                ]
            ]
            await message.reply(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode=enums.ParseMode.HTML)

        elif state == "waiting_format":
            handled = True
            await Seishiro.set_format(message.text)
            await message.reply(get_styled_text("✅ File Name Format Updated!"), parse_mode=enums.ParseMode.HTML)
            await log_activity(client, "SETTINGS", f"📝 <b>Format Updated</b>\n<code>{message.text}</code>", user_id)

        elif state.startswith("waiting_banner_"):
            handled = True
            num = state.split("_")[-1]
            if message.photo:
                await Seishiro.set_config(f"banner_image_{num}", message.photo.file_id)
                await log_activity(client, "SETTINGS", f"🖼️ <b>Banner {num} Updated</b>", user_id)
                
                from Plugins.Settings.media_settings import get_banner_menu
                text, markup = await get_banner_menu(client)
                await message.reply(text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
            else:
                await message.reply("❌ please send a photo.")
                return

        elif state == "waiting_channel":
            handled = True
            try:
                cid = int(message.text)
                await Seishiro.set_default_channel(cid)
                await message.reply(get_styled_text(f"✅ Upload Channel Set: {cid}"), parse_mode=enums.ParseMode.HTML)
                await log_activity(client, "CHANNEL", f"⬆️ <b>Default Upload Channel Set</b>\n<code>{cid}</code>", user_id)
            except ValueError:
                await message.reply("❌ invalid channel id. send a number like -100...")
                return

        elif state == "waiting_dump_channel":
            handled = True
            try:
                cid = int(message.text)
                await Seishiro.set_config("dump_channel", cid)
                await message.reply(get_styled_text(f"✅ Dump Channel Set: {cid}"), parse_mode=enums.ParseMode.HTML)
                await log_activity(client, "CHANNEL", f"💾 <b>Dump Channel Set</b>\n<code>{cid}</code>", user_id)
            except ValueError:
                await message.reply("❌ invalid id.")
                return

        elif state == "waiting_log_channel":
            handled = True
            try:
                cid = int(message.text)
                # Verify channel access
                try:
                    chat = await client.get_chat(cid)
                    title = chat.title
                except Exception:
                    await message.reply("❌ Bot cannot access this channel. Make sure it is admin there!")
                    return
                
                await Seishiro.set_config("log_channel", cid)
                await message.reply(get_styled_text(f"✅ Log Channel Set: {title} ({cid})"), parse_mode=enums.ParseMode.HTML)
                
                # Test the log channel
                await log_activity(client, "SUCCESS", "📊 <b>Log Channel Configured via UI</b>", user_id)
            except ValueError:
                await message.reply("❌ Invalid channel ID format.")
                return

        elif state == "waiting_auc_id":
            handled = True
            try:
                cid = int(message.text)
                try:
                    chat = await client.get_chat(cid)
                    title = chat.title
                except Exception as e:
                    await message.reply(f"❌ <b>error:</b> bot cannot access channel or invalid id.\n`{e}`", parse_mode=enums.ParseMode.HTML)
                    return
                
                await Seishiro.add_auto_update_channel(cid, title)
                await log_activity(client, "CHANNEL", f"🤖 <b>Auto Update Channel Added</b>\n<b>Title:</b> {title}\n<b>ID:</b> <code>{cid}</code>", user_id)
                
                
                curr_list = await Seishiro.get_auto_update_channels()
                list_text = "\n".join([f"• {c.get('title', 'Unknown')} (`{c.get('_id')}`)" for c in curr_list])
                
                text = get_styled_text(
                    f"✅ Added Auto Update Channel:\n{title} ({cid})\n\n"
                    f"<b>Current List:</b>\n{list_text}"
                )
                
                buttons = [[InlineKeyboardButton("🔙 back to list", callback_data="header_auto_update_channels")]]
                await message.reply(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode=enums.ParseMode.HTML)

            except ValueError:
                await message.reply("❌ invalid id format.")
                return
        
        elif state == "waiting_password":
            handled = True
            if message.text.upper() == "OFF":
                await Seishiro.set_config("pdf_password", None)
                await message.reply(get_styled_text("✅ Password Protection Disabled."), parse_mode=enums.ParseMode.HTML)
            else:
                await Seishiro.set_config("pdf_password", message.text)
                await message.reply(get_styled_text(f"✅ Password Set: {message.text}"), parse_mode=enums.ParseMode.HTML)

        elif state == "waiting_merge_size":
            try:
                size = int(message.text)
                await Seishiro.set_config("merge_size_limit", size)
                await message.reply(get_styled_text(f"✅ Merge Size Limit: {size}MB"), parse_mode=enums.ParseMode.HTML)
            except ValueError:
                await message.reply("❌ send a number.")
                return

        elif state == "waiting_regex":
            handled = True
            await Seishiro.set_config("filename_regex", message.text)
            await message.reply(get_styled_text("✅ Regex Pattern Saved."), parse_mode=enums.ParseMode.HTML)

        elif state == "waiting_update_text":
            handled = True
            await Seishiro.set_config("update_text", message.text)
            await message.reply(get_styled_text("✅ Update Text Saved."), parse_mode=enums.ParseMode.HTML)
            
        elif state == "waiting_interval":
            handled = True
            try:
                val = int(message.text)
                if not (60 <= val <= 3600):
                    await message.reply("❌ value out of range (60-3600).")
                    return

                if await Seishiro.set_check_interval(val):
                    await message.reply(get_styled_text(f"✅ Check Interval Set: {val}s"), parse_mode=enums.ParseMode.HTML)
                else:
                    await message.reply("❌ error setting interval.")
            except ValueError:
                await message.reply("❌ invalid number.")

        elif state == "waiting_fsub_id":
            handled = True
            try:
                cid = int(message.text)
                try:
                    await client.get_chat(cid) # Verify access
                except:
                    await message.reply("❌ bot cannot access this channel. add bot as admin first!")
                    return
                
                await Seishiro.add_fsub_channel(cid)
                await message.reply(get_styled_text(f"✅ FSub Channel Added: {cid}"), parse_mode=enums.ParseMode.HTML)
                await log_activity(client, "CHANNEL", f"📢 <b>FSub Channel Added</b>\n<code>{cid}</code>", user_id)
            except ValueError:
                await message.reply("❌ invalid id.")

        elif state == "waiting_fsub_rem_id":
            handled = True
            try:
                cid = int(message.text)
                if await Seishiro.remove_fsub_channel(cid):
                     await message.reply(get_styled_text(f"✅ FSub Channel Removed: {cid}"), parse_mode=enums.ParseMode.HTML)
                else:
                     await message.reply("❌ channel not found in fsub list.")
            except ValueError:
                await message.reply("❌ invalid id.")

        elif state == "waiting_wm_text":
            handled = True
            wm = await Seishiro.get_watermark() or {}
            await Seishiro.set_watermark(
                text=message.text,
                position=wm.get("position", "bottom-right"),
                color=wm.get("color", "#FFFFFF"),
                opacity=wm.get("opacity", 128),
                font_size=wm.get("font_size", 20)
            )
            await message.reply(get_styled_text("✅ Watermark Text Updated!"), parse_mode=enums.ParseMode.HTML)

        elif state == "waiting_wm_color":
            handled = True
            color = message.text
            if not color.startswith("#") or len(color) not in [4, 7]:
                 await message.reply("❌ invalid format. use #rrggbb (e.g. #ff0000).")
                 return
            
            wm = await Seishiro.get_watermark() or {}
            await Seishiro.set_watermark(
                text=wm.get("text", "Default"),
                position=wm.get("position", "bottom-right"),
                color=color,
                opacity=wm.get("opacity", 128),
                font_size=wm.get("font_size", 20)
            )
            await message.reply(get_styled_text(f"✅ Color Set: {color}"), parse_mode=enums.ParseMode.HTML)

        elif state == "waiting_wm_opacity":
            handled = True
            try:
                op = int(message.text)
                if not (0 <= op <= 255): raise ValueError
                
                wm = await Seishiro.get_watermark() or {}
                await Seishiro.set_watermark(
                    text=wm.get("text", "Default"),
                    position=wm.get("position", "bottom-right"),
                    color=wm.get("color", "#FFFFFF"),
                    opacity=op,
                    font_size=wm.get("font_size", 20)
                )
                await message.reply(get_styled_text(f"✅ Opacity Set: {op}"), parse_mode=enums.ParseMode.HTML)
            except:
                await message.reply("❌ invalid number (0-255).")

        elif state == "waiting_deltimer":
            handled = True
            try:
                val = int(message.text)
                await Seishiro.set_del_timer(val)
                await message.reply(get_styled_text(f"✅ Delete Timer Set: {val}s"), parse_mode=enums.ParseMode.HTML)
            except ValueError:
                await message.reply("❌ invalid number.")

        elif state == "waiting_thumb":
            if message.photo:
                file_id = message.photo.file_id
                file_unique_id = message.photo.file_unique_id
                await Seishiro.set_thumbnail(file_id, file_unique_id)
                await message.reply(get_styled_text("✅ Custom Thumbnail Set!"), parse_mode=enums.ParseMode.HTML)
            else:
                await message.reply("❌ please send a photo.")
                return

        elif state in ["waiting_channel_stickers", "waiting_update_sticker"]:
            val = None
            if message.sticker:
                val = message.sticker.file_id
            elif message.text:
                txt = message.text.strip()
                if len(txt) > 10: 
                    val = txt
            
            if not val:
                await message.reply("❌ invalid input. please send a sticker or a valid file id string.")
                return

            key = state.replace("waiting_", "")
            await Seishiro.set_config(key, val)
            await message.reply(get_styled_text(f"✅ {key.replace('_', ' ').title()} Saved.\nID: `{val}`"), parse_mode=enums.ParseMode.HTML)

        elif state == "waiting_add_admin":
            handled = True
            try:
                new_admin_id = int(message.text)
                await Seishiro.add_admin(new_admin_id)
                await message.reply(get_styled_text(f"✅ User {new_admin_id} added as Admin."), parse_mode=enums.ParseMode.HTML)
                await log_activity(client, "ADMIN", f"👑 <b>New Admin Added</b>\n<b>ID:</b> <code>{new_admin_id}</code>", user_id)
            except ValueError:
                await message.reply("❌ invalid user id.")
            except Exception as e:
                await message.reply(f"❌ error: {e}")

        elif state == "waiting_del_admin":
            handled = True
            try:
                del_id = int(message.text)
                if del_id == Config.USER_ID:
                    await message.reply("❌ cannot remove owner.")
                else:
                    await Seishiro.remove_admin(del_id)
                    await message.reply(get_styled_text(f"✅ User {del_id} removed from Admins."), parse_mode=enums.ParseMode.HTML)
                    await log_activity(client, "ADMIN", f"➖ <b>Admin Removed</b>\n<b>ID:</b> <code>{del_id}</code>", user_id)
            except ValueError:
                await message.reply("❌ invalid user id.")
            except Exception as e:
                await message.reply(f"❌ error: {e}")

        elif state == "waiting_broadcast_msg":
            handled = True
             try:
                status_msg = await message.reply("🚀 preparing broadcast...")
                all_users = await Seishiro.get_all_users()
                total = len(all_users)
                successful = 0
                unsuccessful = 0
                
                for user_id in all_users:
                    try:
                        await message.copy(chat_id=user_id)
                        successful += 1
                    except Exception:
                        unsuccessful += 1
                        
                    if (successful + unsuccessful) % 20 == 0:
                        try:
                            await status_msg.edit(f"🚀 Broadcasting... {successful}/{total} sent.")
                        except:
                            pass
                
                await status_msg.edit(
                    f"❌ Failed: {unsuccessful}"
                )
                await log_activity(client, "ADMIN", f"📢 <b>Broadcast Sent</b>\n<b>Total:</b> {total}\n<b>Success:</b> {successful}\n<b>Failed:</b> {unsuccessful}", user_id)
             except Exception as e:
                await message.reply(f"❌ broadcast error: {e}")

        elif state == "waiting_ban_id":
            handled = True
            try:
                target_id = int(message.text)
                if target_id == Config.USER_ID or target_id == message.from_user.id:
                     await message.reply("❌ cannot ban owner or self.")
                else:
                    if await Seishiro.ban_user(target_id):
                        await message.reply(get_styled_text(f"🚫 User {target_id} has been BANNED."), parse_mode=enums.ParseMode.HTML)
                        await log_activity(client, "BAN", f"🚫 <b>User Banned</b>\n<b>ID:</b> <code>{target_id}</code>", user_id)
                    else:
                        await message.reply("❌ failed to ban user.")
            except ValueError:
                await message.reply("❌ invalid user id.")

        elif state == "waiting_unban_id":
            handled = True
            try:
                target_id = int(message.text)
                if await Seishiro.unban_user(target_id):
                    await message.reply(get_styled_text(f"✅ User {target_id} has been UNBANNED."), parse_mode=enums.ParseMode.HTML)
                    await log_activity(client, "UNBAN", f"✅ <b>User Unbanned</b>\n<b>ID:</b> <code>{target_id}</code>", user_id)
                else:
                    await message.reply("❌ failed to unban user.")
            except ValueError:
                await message.reply("❌ invalid user id.")

        else:
            # If no state matched, continue propagation
            message.continue_propagation()
            return
    except Exception as e:
        await message.reply(f"❌ Error: {e}")
    finally:
        # Only cleanup if it was handled and is a settings-related state
        if handled and user_id in user_states:
            curr_state = user_states[user_id].get("state") if isinstance(user_states[user_id], dict) else None
            if curr_state != "WAITING_CHAPTER_INPUT":
                del user_states[user_id]


