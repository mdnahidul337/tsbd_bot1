import logging
import datetime
import random
from functools import wraps
import json
import os
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.constants import ChatMemberStatus, ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
from telegram.error import BadRequest

# --- CONFIGURATION ---

TOKEN = '7643025446:AAHPQgytUtqHz_wB-9y-OziM8aucimPvThw'  # Replace with your bot token

ADMIN_ID = 6017525126  # Replace with your Telegram user ID

GROUP_ID = -1002221622835  # Replace with your Telegram group ID (must be a supergroup)

GROUP_LINK = "https://t.me/BDTrainSimulator24RahamatStudio"

game_data = {
    "version": "v1.0.5",
    "download_link": "https://play.google.com/store/apps/details?id=com.RahamatStudio.TrainSimulatorBangladesh&hl=en_US",
    "maintenance": False,
    "server_region": "South Asia (Bangladesh)",
    "Type": "Release",
    "auto_delete": True
}

# --- PERSISTENCE ---
DATA_FILE = 'bot_data.json'

def load_persist_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error loading data: {e}")
    return {
        "whitelist": [],
        "blacklist": [],
        "bad_words": ["badword1", "badword2"], # Initial examples
        "warnings": {}
    }

def save_persist_data():
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(bot_persist, f, indent=4)
    except Exception as e:
        logging.error(f"Error saving data: {e}")

bot_persist = load_persist_data()

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- SECURITY GATEKEEPER ---
def restricted(func):
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id == ADMIN_ID: return await func(update, context, *args, **kwargs)
        if game_data["maintenance"]:
            await update.message.reply_text("🚧 <b>SYSTEM UNDER MAINTENANCE</b>\nOur engineers are working on the tracks. Please check back later.", parse_mode=ParseMode.HTML)
            return

        # Optimization: If command is sent inside the group, allow it immediately
        if update.effective_chat.id == GROUP_ID:
            return await func(update, context, *args, **kwargs)

        try:
            member = await context.bot.get_chat_member(chat_id=GROUP_ID, user_id=user_id)
            if member.status in [ChatMemberStatus.LEFT, ChatMemberStatus.BANNED]:
                await update.message.reply_text(f"👋 <b>Access Denied!</b>\nYou must be in our official group to use this bot.\n\n🔗 <a href='{GROUP_LINK}'>Join Group</a>", parse_mode=ParseMode.HTML)
                return
            return await func(update, context, *args, **kwargs)
        except BadRequest:
            await update.message.reply_text("⚠️ <b>Configuration Error</b>\nI cannot verify group membership. Please make sure I am an <b>Admin</b> in the group!", parse_mode=ParseMode.HTML)
        except Exception as e:
            await update.message.reply_text(f"⚠️ <b>System Error:</b> {e}", parse_mode=ParseMode.HTML)
    return wrapped

# --- NEW UTILITY TOOLS ---

@restricted
async def ping_server(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Simulates checking game server latency"""
    ms = random.randint(20, 150)
    status = "🟢 Excellent" if ms < 60 else "🟡 Average"
    await update.message.reply_text(
        f"📡 <b>Server Latency Check</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📍 Region: <code>{game_data['server_region']}</code>\n"
        f"⚡ Ping: <b>{ms}ms</b>\n"
        f"📊 Status: {status}\n"
        f"━━━━━━━━━━━━━━━━━━", parse_mode=ParseMode.HTML)

@restricted
async def suggest_feature(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Users can send suggestions directly to you"""
    if not context.args:
        await update.message.reply_text("💡 <b>Usage:</b> <code>/suggest add a Hino AK1J engine</code>", parse_mode=ParseMode.HTML)
        return
    suggestion = " ".join(context.args)
    await context.bot.send_message(chat_id=ADMIN_ID, text=f"💡 <b>NEW SUGGESTION</b>\nFrom: @{update.effective_user.username}\nIdea: {suggestion}", parse_mode=ParseMode.HTML)
    await update.message.reply_text("✅ <b>Thank you!</b> Your idea has been sent to the developer.")

async def delete_message_job(context: ContextTypes.DEFAULT_TYPE):
    """Job to delete a message after a delay"""
    job = context.job
    try:
        await context.bot.delete_message(chat_id=job.chat_id, message_id=job.data)
    except Exception:
        pass

# --- ADMIN TOOLS ---

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin can send a formatted news alert to the group"""
    if update.effective_user.id != ADMIN_ID or not context.args: return
    news = " ".join(context.args)
    msg = (
        "📢 <b>OFFICIAL ANNOUNCEMENT</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"{news}\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "<i>Stay tuned for more updates!</i>"
    )
    await context.bot.send_message(chat_id=GROUP_ID, text=msg, parse_mode=ParseMode.HTML)

async def update_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or not context.args: return
    game_data["download_link"] = context.args[0]
    await update.message.reply_text(f"🔗 <b>Link Synced!</b>\nNew URL: <code>{game_data['download_link']}</code>", parse_mode=ParseMode.HTML)

async def update_version(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or not context.args: return
    game_data["version"] = context.args[0]
    await update.message.reply_text(f"📦 <b>Version Updated!</b>\nNew Version: <code>{game_data['version']}</code>", parse_mode=ParseMode.HTML)

async def update_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or not context.args: return
    game_data["Type"] = context.args[0]
    await update.message.reply_text(f"🏷️ <b>Type Updated!</b>\nNew Type: <code>{game_data['Type']}</code>", parse_mode=ParseMode.HTML)

async def toggle_maintenance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    game_data["maintenance"] = not game_data["maintenance"]
    status = "ON 🔴" if game_data["maintenance"] else "OFF 🟢"
    await update.message.reply_text(f"🔧 <b>Maintenance Mode:</b> {status}", parse_mode=ParseMode.HTML)

async def toggle_autodelete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    game_data["auto_delete"] = not game_data.get("auto_delete", True)
    status = "ON 🟢" if game_data["auto_delete"] else "OFF 🔴"
    await update.message.reply_text(f"⏱️ <b>Auto-Delete Links:</b> {status}\n(Links delete after 10 mins)", parse_mode=ParseMode.HTML)

async def send_dm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a direct message to a user ID"""
    if update.effective_user.id != ADMIN_ID: return
    if len(context.args) < 2:
        await update.message.reply_text("⚠️ <b>Usage:</b> <code>/dm [user_id] [message]</code>", parse_mode=ParseMode.HTML)
        return
    
    user_id = context.args[0]
    message = " ".join(context.args[1:])
    
    try:
        await context.bot.send_message(chat_id=user_id, text=f"📨 <b>Admin Message:</b>\n\n{message}", parse_mode=ParseMode.HTML)
        await update.message.reply_text(f"✅ Message sent to <code>{user_id}</code>", parse_mode=ParseMode.HTML)
    except Exception as e:
        await update.message.reply_text(f"❌ <b>Failed:</b> {e}", parse_mode=ParseMode.HTML)

async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ban a user from the group by ID"""
    if update.effective_user.id != ADMIN_ID: return
    if not context.args:
        await update.message.reply_text("⚠️ <b>Usage:</b> <code>/ban [user_id]</code>", parse_mode=ParseMode.HTML)
        return
        
    try:
        await context.bot.ban_chat_member(chat_id=GROUP_ID, user_id=int(context.args[0]))
        await update.message.reply_text(f"🚫 <b>Banned User:</b> <code>{context.args[0]}</code>", parse_mode=ParseMode.HTML)
    except Exception as e:
        await update.message.reply_text(f"❌ <b>Failed:</b> {e}", parse_mode=ParseMode.HTML)

async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unban a user from the group by ID"""
    if update.effective_user.id != ADMIN_ID: return
    if not context.args:
        await update.message.reply_text("⚠️ <b>Usage:</b> <code>/unban [user_id]</code>", parse_mode=ParseMode.HTML)
        return
        
    try:
        await context.bot.unban_chat_member(chat_id=GROUP_ID, user_id=int(context.args[0]))
        await update.message.reply_text(f"✅ <b>Unbanned User:</b> <code>{context.args[0]}</code>", parse_mode=ParseMode.HTML)
    except Exception as e:
        await update.message.reply_text(f"❌ <b>Failed:</b> {e}", parse_mode=ParseMode.HTML)

async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mute a user for a specific duration (minutes)"""
    if update.effective_user.id != ADMIN_ID: return
    
    if len(context.args) < 2:
        await update.message.reply_text("🔇 <b>Usage:</b> <code>/mute [user_id] [minutes]</code>", parse_mode=ParseMode.HTML)
        return

    try:
        user_id = int(context.args[0])
        minutes = int(context.args[1])
        
        # Telegram requires restriction to be at least 30 seconds in the future
        if minutes < 1: minutes = 1
        
        until_date = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
        permissions = ChatPermissions(can_send_messages=False)
        
        await context.bot.restrict_chat_member(
            chat_id=GROUP_ID,
            user_id=user_id,
            permissions=permissions,
            until_date=until_date
        )
        await update.message.reply_text(f"🔇 <b>Muted User:</b> <code>{user_id}</code> for {minutes} mins.", parse_mode=ParseMode.HTML)
    except Exception as e:
        await update.message.reply_text(f"❌ <b>Failed:</b> {e}", parse_mode=ParseMode.HTML)

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get ID of the user you reply to or your own"""
    if not update.message.reply_to_message:
        await update.message.reply_text(f"🆔 Your ID: <code>{update.effective_user.id}</code>", parse_mode=ParseMode.HTML)
        return
    
    target = update.message.reply_to_message.from_user
    await update.message.reply_text(f"👤 <b>User Info:</b>\nName: {target.full_name}\nID: <code>{target.id}</code>", parse_mode=ParseMode.HTML)

async def create_poll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Create a poll in the group"""
    if update.effective_user.id != ADMIN_ID: return
    
    if not context.args:
        await update.message.reply_text("📊 <b>Usage:</b> <code>/poll Question | Option1 | Option2</code>", parse_mode=ParseMode.HTML)
        return

    text = " ".join(context.args)
    parts = [p.strip() for p in text.split('|')]
    
    question = parts[0]
    options = parts[1:] if len(parts) > 1 else ["Yes", "No"]
    
    if len(options) < 2:
        await update.message.reply_text("⚠️ <b>Error:</b> A poll needs at least 2 options.", parse_mode=ParseMode.HTML)
        return

    try:
        await context.bot.send_poll(
            chat_id=GROUP_ID,
            question=question,
            options=options,
            is_anonymous=False
        )
        await update.message.reply_text("✅ <b>Poll Created!</b>", parse_mode=ParseMode.HTML)
    except Exception as e:
        await update.message.reply_text(f"❌ <b>Failed:</b> {e}", parse_mode=ParseMode.HTML)

# --- NEW FILTER & LIST COMMANDS ---

async def handle_list_management(update: Update, context: ContextTypes.DEFAULT_TYPE, list_type: str, action: str):
    """Generic helper for whitelist/blacklist management"""
    if update.effective_user.id != ADMIN_ID: return
    
    target_id = None
    if update.message.reply_to_message:
        target_id = update.message.reply_to_message.from_user.id
    elif context.args:
        try:
            # Handle @username if possible (not trivial without cached IDs, but we can try)
            arg = context.args[0]
            if arg.startswith('@'):
                await update.message.reply_text("⚠️ Please reply to the user's message or provide their numeric ID.")
                return
            target_id = int(arg)
        except ValueError:
            await update.message.reply_text("⚠️ Invalid ID.")
            return

    if not target_id:
        await update.message.reply_text(f"⚠️ Reply to a user or provide an ID: <code>/{action}{list_type} [id]</code>", parse_mode=ParseMode.HTML)
        return

    if action == "add":
        if target_id not in bot_persist[list_type]:
            bot_persist[list_type].append(target_id)
            save_persist_data()
            await update.message.reply_text(f"✅ User <code>{target_id}</code> added to <b>{list_type}</b>.", parse_mode=ParseMode.HTML)
        else:
            await update.message.reply_text(f"ℹ️ User is already in <b>{list_type}</b>.", parse_mode=ParseMode.HTML)
    else: # action == "remove"
        if target_id in bot_persist[list_type]:
            bot_persist[list_type].remove(target_id)
            save_persist_data()
            await update.message.reply_text(f"✅ User <code>{target_id}</code> removed from <b>{list_type}</b>.", parse_mode=ParseMode.HTML)
        else:
            await update.message.reply_text(f"ℹ️ User not found in <b>{list_type}</b>.", parse_mode=ParseMode.HTML)

async def whitelist_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_list_management(update, context, "whitelist", "add")

async def unwhitelist_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_list_management(update, context, "whitelist", "remove")

async def blacklist_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_list_management(update, context, "blacklist", "add")

async def unblacklist_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_list_management(update, context, "blacklist", "remove")

async def view_whitelist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    l = bot_persist["whitelist"]
    text = "🛡️ <b>WHITELISTED USERS:</b>\n" + ("\n".join([f"• <code>{uid}</code>" for uid in l]) if l else "<i>(Empty)</i>")
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def view_blacklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    l = bot_persist["blacklist"]
    text = "🚫 <b>BLACKLISTED USERS:</b>\n" + ("\n".join([f"• <code>{uid}</code>" for uid in l]) if l else "<i>(Empty)</i>")
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def add_bad_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or not context.args: return
    word = context.args[0].lower()
    if word not in bot_persist["bad_words"]:
        bot_persist["bad_words"].append(word)
        save_persist_data()
        await update.message.reply_text(f"✅ Added <code>{word}</code> to filter.", parse_mode=ParseMode.HTML)

async def del_bad_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or not context.args: return
    word = context.args[0].lower()
    if word in bot_persist["bad_words"]:
        bot_persist["bad_words"].remove(word)
        save_persist_data()
        await update.message.reply_text(f"✅ Removed <code>{word}</code> from filter.", parse_mode=ParseMode.HTML)

async def view_bad_words(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    l = bot_persist["bad_words"]
    text = "🙊 <b>FILTERED WORDS:</b>\n" + (", ".join(l) if l else "<i>(None)</i>")
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

# --- FILTERING LOGIC ---

async def message_filter_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main filtering logic for links and bad words"""
    if not update.message or not update.message.text: return
    
    # Only filter in the designated group
    if update.effective_chat.id != GROUP_ID: return
    
    user = update.effective_user
    user_id = user.id
    
    # ADMINS and WHITELISTED users skip filters
    if user_id == ADMIN_ID or user_id in bot_persist["whitelist"]:
        return

    # Check if user is blacklisted
    if user_id in bot_persist["blacklist"]:
        try:
            await update.message.delete()
            return # Don't process further
        except Exception: pass

    text = update.message.text.lower()
    
    # 1. LINK FILTERING (Only Admin/Whitelisted can send links)
    has_link = False
    if update.message.entities:
        for entity in update.message.entities:
            if entity.type in ["url", "text_link"]:
                has_link = True
                break
    
    if not has_link and re.search(r'(https?://|www\.)\S+', text):
        has_link = True
        
    if has_link:
        try:
            await update.message.delete()
            # Optionally warn user? Link filtering is usually strict.
            # await update.message.reply_text(f"🚫 {user.mention_html()}, links are not allowed in this group!", parse_mode=ParseMode.HTML)
            return
        except Exception: pass

    # 2. WORD FILTERING
    found_word = False
    for word in bot_persist["bad_words"]:
        if word in text:
            found_word = True
            break
            
    if found_word:
        try:
            await update.message.delete()
            
            # Warning System
            u_id = str(user_id)
            bot_persist["warnings"][u_id] = bot_persist["warnings"].get(u_id, 0) + 1
            warn_count = bot_persist["warnings"][u_id]
            save_persist_data()
            
            if warn_count <= 2:
                await update.message.reply_text(
                    f"⚠️ <b>WARNING {warn_count}/2</b>\n"
                    f"{user.mention_html()}, bad words are strictly prohibited in this group!", 
                    parse_mode=ParseMode.HTML)
            else:
                # Mute Logic
                mute_time = 15 if warn_count == 3 else 10
                until_date = datetime.datetime.now() + datetime.timedelta(minutes=mute_time)
                
                permissions = ChatPermissions(can_send_messages=False)
                await context.bot.restrict_chat_member(
                    chat_id=GROUP_ID,
                    user_id=user_id,
                    permissions=permissions,
                    until_date=until_date
                )
                
                await update.message.reply_text(
                    f"🔇 <b>USER MUTED</b>\n"
                    f"{user.mention_html()} has been muted for <b>{mute_time} minutes</b> for repeated violations.",
                    parse_mode=ParseMode.HTML)
            return
        except Exception as e:
            logging.error(f"Filter error: {e}")

# --- USER INTERFACE IMPROVEMENTS ---

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show available commands based on user role"""
    user_id = update.effective_user.id
    
    help_text = (
        "🤖 <b>COMMAND CENTER</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "<b>👤 User Commands:</b>\n"
        "• <code>/status</code> - Check system status\n"
        "• <code>/download</code> - Get latest version\n"
        "• <code>/ping</code> - Check server latency\n"
        "• <code>/suggest [idea]</code> - Submit feedback\n"
        "   <i>Ex: /suggest Add night mode</i>\n"
    )
    
    if user_id == ADMIN_ID:
        help_text += (
            "\n<b>👮‍♂️ Admin Tools:</b>\n"
            "• <code>/linkup [url]</code> - Update download link\n"
            "• <code>/ver [code]</code> - Update version\n"
            "• <code>/type [name]</code> - Update build type\n"
            "• <code>/announce [msg]</code> - Broadcast to group\n"
            "• <code>/maint</code> - Toggle maintenance mode\n"
            "• <code>/autodel</code> - Toggle link auto-delete\n"
            "• <code>/dm [id] [msg]</code> - Send private message\n"
            "   <i>Ex: /dm 123456 Hello there</i>\n"
            "• <code>/ban [id]</code> - Ban user\n"
            "• <code>/unban [id]</code> - Unban user\n"
            "• <code>/mute [id] [min]</code> - Mute user\n"
            "• <code>/whitelist [id]</code> - Whitelist user\n"
            "• <code>/blacklist [id]</code> - Blacklist user\n"
            "• <code>/viewwhitelist</code> - See whitelist\n"
            "• <code>/viewblacklist</code> - See blacklist\n"
            "• <code>/addword [word]</code> - Add bad word\n"
            "• <code>/delword [word]</code> - Remove bad word\n"
            "• <code>/viewwords</code> - List bad words\n"
            "• <code>/poll [Q]|[O1]|[O2]</code> - Create poll\n"
            "   <i>Ex: /poll Vote? | Yes | No</i>\n"
            "• <code>/id</code> - Get User ID (Reply to msg)\n"
        )
        
    help_text += "━━━━━━━━━━━━━━━━━━"
    
    await update.message.reply_text(help_text, parse_mode=ParseMode.HTML)

@restricted
async def show_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    m_icon = "🔴" if game_data["maintenance"] else "🟢"
    # Visual Progress Bar
    progress = "■■■■■■■■□□" # 80% stable example
    status_msg = (
        "📊 <b>TRAIN SYSTEM CORE</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"🔌 System Status: {m_icon} <b>Active</b>\n"
        f"📦 Version: <code>{game_data['version']}</code>\n"
        f"⚙️ Stability: [<code>{progress}</code>] 80%\n"
        f"👥 Group: <a href='{GROUP_LINK}'>Official Community</a>\n"
        "━━━━━━━━━━━━━━━━━━"
    )
    await update.message.reply_text(status_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

@restricted
async def get_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg_text = (
        "<b>📥 DOWNLOAD CENTER</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Click the button below to get the latest build. Ensure you have 500MB free space.\n\n"
        f"🚆 <b>Current Build:</b> <code>{game_data['version']}</code>"
    )
    if game_data.get("auto_delete", True):
        msg_text += "\n\n⚠️ <i>Link expires in 10 minutes.</i>"

    keyboard = [[InlineKeyboardButton("⬇️ DOWNLOAD NOW", url=game_data["download_link"])]]
    sent_msg = await update.message.reply_text(msg_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

    if game_data.get("auto_delete", True):
        context.job_queue.run_once(delete_message_job, 600, chat_id=sent_msg.chat_id, data=sent_msg.message_id)

# --- START ---
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    
    # User Commands
    app.add_handler(CommandHandler("start", show_status))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", show_status))
    app.add_handler(CommandHandler("download", get_download))
    app.add_handler(CommandHandler("ping", ping_server))
    app.add_handler(CommandHandler("suggest", suggest_feature))
    
    # Admin Commands
    app.add_handler(CommandHandler("linkup", update_link))
    app.add_handler(CommandHandler("announce", broadcast))
    app.add_handler(CommandHandler("ver", update_version))
    app.add_handler(CommandHandler("type", update_type))
    app.add_handler(CommandHandler("maint", toggle_maintenance))
    app.add_handler(CommandHandler("autodel", toggle_autodelete))
    app.add_handler(CommandHandler("dm", send_dm))
    app.add_handler(CommandHandler("ban", ban_user))
    app.add_handler(CommandHandler("unban", unban_user))
    app.add_handler(CommandHandler("mute", mute_user))
    app.add_handler(CommandHandler("id", get_id))
    app.add_handler(CommandHandler("poll", create_poll))

    # New Filter & List Commands
    app.add_handler(CommandHandler("whitelist", whitelist_user))
    app.add_handler(CommandHandler("unwhitelist", unwhitelist_user))
    app.add_handler(CommandHandler("blacklist", blacklist_user))
    app.add_handler(CommandHandler("unblacklist", unblacklist_user))
    app.add_handler(CommandHandler("viewwhitelist", view_whitelist))
    app.add_handler(CommandHandler("viewblacklist", view_blacklist))
    app.add_handler(CommandHandler("addword", add_bad_word))
    app.add_handler(CommandHandler("delword", del_bad_word))
    app.add_handler(CommandHandler("viewwords", view_bad_words))

    # Global Message Filter (must be checked for all messages in group)
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), message_filter_handler))
    
    print("🚀 Advanced Train Bot Online!")
    app.run_polling()