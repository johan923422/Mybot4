import telebot
import threading
import os
import time
from telebot.types import ChatPermissions
from googletrans import Translator

# ---------------- BOT TOKENS ----------------
TOKENS = [
    os.getenv("BOT1"),
    os.getenv("BOT2"),
    os.getenv("BOT3"),
    os.getenv("BOT4")
]

# ---------------- OPENAI ----------------
import openai
openai.api_key = os.getenv("OPENAI_KEY")

# ---------------- OWNER & BOT ADMINS ----------------
OWNER_ID = 7887055769           # Replace with your Telegram ID
BOT_ADMINS = [987654321, 112233445]  # Replace with bot admin IDs

def is_admin_or_owner(user_id):
    return user_id == OWNER_ID or user_id in BOT_ADMINS

# ---------------- GP CHATS ----------------
GP_CHAT_IDS = [-1001111111111, -1002222222222, -1003333333333]  # Add GP chat IDs

# ---------------- Shared resources ----------------
FILTER_WORDS = ["badword1", "badword2"]  # Add filtered words
spam_speed = {}
spam_running = {}
last_doc = {}
call_running = {}
translator = Translator()

# ---------------- DEFAULT SPAM TEXT ----------------
SPAM_TEXT = """
ဘာပုတယ်ညာပုတယ်နဲ့ဉာဏ်ရည်ကမမှီဘူး
မင်းဉာဏ်ရည်နဲ့ကျမ်းတိုက်ဖုန်သုပ်တောင်ရမယ့်ကောင်မဟုတ်ဘူး
ကြောက်လို့လက်တုန်နေပြီလား
ညီပုပြေးတော့မလို့လား
မင်းအဆင့်လောက်နဲ့ငါကို ယှဉ်နိုင်မှာလဲမဟုတ်ပါဘူး
ခွေးလေးကိုက်စမ်း
မင်းအမေကဖာသည်မကြီးဆို
ဘာလဲမင်းအမေကိုငါမလိုးပေးလို့လောင်တာလား
စောက်ခြောက်လိုလုပ်မနေနဲ့ကြာတယ်
ကိုက်စမ်းဖာပြက်မသား
"""

# ---------------- MONOBOX MESSAGE ----------------
def monobox_message(user, text):
    return f"📦 <b>File Broadcast</b>\n👤 From: {user.first_name}\n📝 Content:\n<pre>{text}</pre>"

# ---------------- BOT START FUNCTION ----------------
def start_bot(token):
    bot = telebot.TeleBot(token, parse_mode="HTML")

    def delete_cmd(message):
        try:
            bot.delete_message(message.chat.id, message.message_id)
        except:
            pass

    # ---------------- AUTO WELCOME ----------------
    @bot.message_handler(content_types=['new_chat_members'])
    def welcome(message):
        for user in message.new_chat_members:
            profile_link = f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"
            caption_text = f"{profile_link}\nဟုတ်ကဲ့ {user.first_name} သည် {message.chat.title} သို့ဝင်လာပါသည်"
            photos = bot.get_user_profile_photos(user.id)
            if photos.total_count > 0:
                file_id = photos.photos[0][-1].file_id
                bot.send_photo(message.chat.id, file_id, caption=caption_text, parse_mode="HTML")
            else:
                bot.send_message(message.chat.id, caption_text, parse_mode="HTML", disable_web_page_preview=True)

    # ---------------- AUTO GOODBYE ----------------
    @bot.message_handler(content_types=['left_chat_member'])
    def goodbye(message):
        user = message.left_chat_member
        profile_link = f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"
        caption_text = f"{profile_link}\nဟုတ်ကဲ့ {user.first_name} သည် {message.chat.title} မှထွက်သွားပါပြီ"
        photos = bot.get_user_profile_photos(user.id)
        if photos.total_count > 0:
            file_id = photos.photos[0][-1].file_id
            bot.send_photo(message.chat.id, file_id, caption=caption_text, parse_mode="HTML")
        else:
            bot.send_message(message.chat.id, caption_text, parse_mode="HTML", disable_web_page_preview=True)

    # ---------------- MESSAGE HANDLER ----------------
    @bot.message_handler(func=lambda m: True)
    def handler(message):
        if message.chat.type not in ["group", "supergroup"]:
            return

        text = message.text or ""
        chat_id = message.chat.id
        user_id = message.from_user.id

        # ---------- DEFAULT SPAM SPEED ----------
        if chat_id not in spam_speed:
            spam_speed[chat_id] = 2

        # ---------- FILTER WORDS ----------
        for word in FILTER_WORDS:
            if word.lower() in text.lower():
                bot.delete_message(chat_id, message.message_id)
                bot.send_message(chat_id, f"⚠️ {message.from_user.first_name} used a filtered word!")
                return

        # ---------- BLOCK LINKS FOR NON-ADMINS ----------
        if message.entities:
            for ent in message.entities:
                if ent.type in ['url', 'text_link']:
                    try:
                        admins = bot.get_chat_administrators(chat_id)
                        is_user_admin = any(a.user.id == user_id for a in admins)
                    except:
                        is_user_admin = False
                    if not is_user_admin:
                        bot.delete_message(chat_id, message.message_id)
                        bot.send_message(chat_id, f"❌ {message.from_user.first_name} cannot send links!")
                        return

        # ---------- BLOCK FORWARDED ----------
        if message.forward_from or message.forward_from_chat:
            try:
                admins = bot.get_chat_administrators(chat_id)
                is_user_admin = any(a.user.id == user_id for a in admins)
            except:
                is_user_admin = False
            if not is_user_admin:
                bot.delete_message(chat_id, message.message_id)
                bot.send_message(chat_id, f"❌ {message.from_user.first_name} cannot forward messages!")
                return

        # ---------- HELP ----------
        if text == "အကူညီ":
            delete_cmd(message)
            bot.send_message(chat_id, """<pre>
All - memberအကုန်mt
Callone - တစ်ယောက်ဆီအကုန်ခေါ်
Call - active member တွေကိုခေါ်
ရပ် - လူခေါ်ရပ်
Info - idကြည့်(reply)
ပိတ်ထား - mute(reply)
လက်မရားနဲ့ - unmute(reply)
လစ် - kick(reply)
ပြန်မလာနဲ့ - ban(reply)
ပြန်ဝင်ခွင့်ပြု - unban(reply)
အက်မင် - gp(add_admin)(reply)
ရာထူးချ - gp(remove_admin)(reply)
mtရိုက် - tag spam(reply)
ရိုက်သတ် - spam(reply)
အရှိန် 1-5 - spam speed
ခွင့်လွှတ်လိုက် - spam stop
ဘာသာပြန် - translate(reply)
filter - auto delete
file - စာပို့
list - bot admin(owner)
ထည့် - bot admin ထည့်(owner)
ဖြုတ် - bot admin ဖြုတ်(owner)
</pre>""")
            return

        # ---------- LIST ----------
        if text == "list":
            delete_cmd(message)
            if not is_admin_or_owner(user_id):
                bot.reply_to(message, "ခွေးမသားbotသုံးချင်တာလား@Legendary_Johan_Sama အဖေ့ဆီလာ")
                return
            names = [str(uid) for uid in BOT_ADMINS]
            bot.reply_to(message, f"📜 Bot Admins:\nOwner: {OWNER_ID}\nAdmins: {', '.join(names)}")
            return

        # ---------- FILE ----------
        if message.content_type == 'document':
            last_doc[chat_id] = message
            bot.reply_to(message, "ပို့လိုက်ပါပြီသခင် Reply 'file' to broadcast text.")
            return

        if text.lower() == "file":
            delete_cmd(message)
            if not is_admin_or_owner(user_id):
                bot.reply_to(message, "ခွေးမသားbotသုံးချင်တာလား@Legendary_Johan_Sama အဖေ့ဆီလာ")
                return
            if chat_id not in last_doc:
                bot.reply_to(message, "fileမတွေ့ပါဘူးသခင်")
                return
            doc_msg = last_doc[chat_id]
            file_info = bot.get_file(doc_msg.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            try:
                text_content = downloaded_file.decode("utf-8")
            except:
                bot.reply_to(message, "မရဘူး(not a text file).")
                return
            for gp_chat in GP_CHAT_IDS:
                bot.send_message(gp_chat, monobox_message(doc_msg.from_user, text_content))
            bot.reply_to(message, "📤 Document content broadcasted to all GP chats!")
            del last_doc[chat_id]
            return

        # ---------- SPEED ----------
        if text.startswith("အရှိန်"):
            delete_cmd(message)
            try:
                speed = int(text.split()[1])
                if 1 <= speed <= 5:
                    spam_speed[chat_id] = speed
                    bot.send_message(chat_id, f"⚡ Speed set to {speed}")
            except:
                pass
            return

        # ---------- STOP SPAM ----------
        if text == "ခွင့်လွှတ်လိုက်":
            delete_cmd(message)
            spam_running[chat_id] = False
            call_running[chat_id] = False
            return

        # ---------- MT SPAM ----------
        if text == "mtရိုက်" and message.reply_to_message:
            delete_cmd(message)
            if not is_admin_or_owner(user_id):
                return
            user = message.reply_to_message.from_user
            spam_running[chat_id] = True
            def spam():
                while spam_running.get(chat_id):
                    bot.send_message(chat_id, f"<a href='tg://user?id={user.id}'>{user.first_name}</a>\n{SPAM_TEXT}", disable_web_page_preview=True)
                    time.sleep(6 - spam_speed[chat_id])
            threading.Thread(target=spam).start()
            return

        if text == "ရိုက်သတ်" and message.reply_to_message:
            delete_cmd(message)
            if not is_admin_or_owner(user_id):
                return
            spam_running[chat_id] = True
            def spam2():
                while spam_running.get(chat_id):
                    bot.send_message(chat_id, SPAM_TEXT)
                    time.sleep(6 - spam_speed[chat_id])
            threading.Thread(target=spam2).start()
            return

        # ---------- CALL COMMANDS (WITH OPTIONAL TEXT) ----------
        if text.startswith("All"):
            delete_cmd(message)
            if not is_admin_or_owner(user_id):
                return
            msg_text = text[3:].strip() or "Calling all members..."
            for member in bot.get_chat_members(chat_id):
                bot.send_message(chat_id, f"📞 {member.user.first_name}\n{msg_text}")
            return

        if text.startswith("Callone"):
            delete_cmd(message)
            if not is_admin_or_owner(user_id):
                return
            msg_text = text[7:].strip() or "Calling individually..."
            for member in bot.get_chat_members(chat_id):
                bot.send_message(chat_id, f"📞 {member.user.first_name}\n{msg_text}")
                time.sleep(1)
            return

        if text.startswith("Call"):
            delete_cmd(message)
            if not is_admin_or_owner(user_id):
                return
            msg_text = text[4:].strip() or "Calling active members..."
            bot.send_message(chat_id, msg_text)
            return

        if text == "ရပ်":
            delete_cmd(message)
            call_running[chat_id] = False
            return

        # ---------- ADMIN, MUTE, UNMUTE, KICK, BAN, UNBAN ----------
        if text == "အက်မင်" and message.reply_to_message:
            delete_cmd(message)
            if not is_admin_or_owner(user_id):
                return
            bot.promote_chat_member(chat_id, message.reply_to_message.from_user.id,
                                    can_change_info=True, can_delete_messages=True,
                                    can_invite_users=True, can_pin_messages=True,
                                    can_promote_members=True)
            return

        if text == "ရာထူးချ" and message.reply_to_message:
            delete_cmd(message)
            if not is_admin_or_owner(user_id):
                return
            bot.promote_chat_member(chat_id, message.reply_to_message.from_user.id,
                                    can_change_info=False, can_delete_messages=False,
                                    can_invite_users=False, can_pin_messages=False,
                                    can_promote_members=False)
            return

        if text == "လစ်" and message.reply_to_message:
            delete_cmd(message)
            if not is_admin_or_owner(user_id):
                return
            bot.kick_chat_member(chat_id, message.reply_to_message.from_user.id)
            return

        if text == "ပြန်မလာနဲ့" and message.reply_to_message:
            delete_cmd(message)
            if not is_admin_or_owner(user_id):
                return
            bot.ban_chat_member(chat_id, message.reply_to_message.from_user.id)
            return

        if text == "ပြန်ဝင်ခွင့်ပြု" and message.reply_to_message:
            delete_cmd(message)
            if not is_admin_or_owner(user_id):
                return
            bot.unban_chat_member(chat_id, message.reply_to_message.from_user.id)
            return

        if text == "Info" and message.reply_to_message:
            delete_cmd(message)
            if not is_admin_or_owner(user_id):
                return
            bot.reply_to(message, f"👤 {message.reply_to_message.from_user.first_name}\n🆔 {message.reply_to_message.from_user.id}")
            return

        if text == "ပိတ်ထား" and message.reply_to_message:
            delete_cmd(message)
            if not is_admin_or_owner(user_id):
                return
            bot.restrict_chat_member(chat_id, message.reply_to_message.from_user.id, ChatPermissions(can_send_messages=False))
            return

        if text == "လက်မရားနဲ့" and message.reply_to_message:
            delete_cmd(message)
            if not is_admin_or_owner(user_id):
                return
            bot.restrict_chat_member(chat_id, message.reply_to_message.from_user.id, ChatPermissions(can_send_messages=True))
            return

        # ---------- TRANSLATE ----------
        if text.startswith("ဘာသာပြန်") and message.reply_to_message:
            delete_cmd(message)
            if not is_admin_or_owner(user_id):
                return
            translated = translator.translate(message.reply_to_message.text, dest="en")
            bot.send_message(chat_id, translated.text)
            return

    bot.infinity_polling()

# ---------------- START 4 BOTS ----------------
threads = []
for token in TOKENS:
    t = threading.Thread(target=start_bot, args=(token,))
    t.start()
    threads.append(t)

for t in threads:
    t.join()
