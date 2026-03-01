import telebot
import threading
import openai
import os
import time
from telebot.types import ChatPermissions
from deep_translator import GoogleTranslator

# ---------------- BOT TOKENS ----------------
TOKENS = [
    os.getenv("BOT1"),
    os.getenv("BOT2"),
    os.getenv("BOT3"),
    os.getenv("BOT4")
]
OPENAI_KEY = os.getenv("OPENAI_KEY")
openai.api_key = OPENAI_KEY

# ---------------- OWNER & BOT ADMINS ----------------
OWNER_ID = int(os.getenv("OWNER_ID"))
BOT_ADMINS = [987654321, 112233445]  # Bot admin IDs

def is_admin_or_owner(user_id):
    return user_id == OWNER_ID or user_id in BOT_ADMINS

# ---------------- GP CHATS ----------------
GP_CHAT_IDS = [-1001111111111, -1002222222222, -1003333333333]

# ---------------- Shared resources ----------------
FILTER_WORDS = ["badword1","badword2"]
spam_speed = {}
spam_running = {}
call_running = {}
last_doc = {}
translator = GoogleTranslator(source='auto', target='my')

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

def monobox_message(user, text):
    return f"📦 <b>File Broadcast</b>\n👤 From: {user.first_name}\n📝 Content:\n<pre>{text}</pre>"

# ---------------- START BOT ----------------
def start_bot(token):
    bot = telebot.TeleBot(token, parse_mode="HTML")

    def delete_cmd(message):
        try:
            bot.delete_message(message.chat.id, message.message_id)
        except:
            pass

    # ---------------- WELCOME / GOODBYE ----------------
    @bot.message_handler(content_types=['new_chat_members'])
    def welcome(message):
        for user in message.new_chat_members:
            bot.send_message(
                message.chat.id,
                f"{user.first_name}ဖာသည်မသားတစ်ကောင်ဝင်လာတယ်\n🆔 ID: {user.id}"
            )

    @bot.message_handler(content_types=['left_chat_member'])
    def goodbye(message):
        user = message.left_chat_member
        bot.send_message(
            message.chat.id,
            f"{user.first_name} ဖာသည်မသားတစ်ကောင်ထွက်သွားပြီ\n🆔 ID: {user.id}"
        )

    # ---------------- MAIN HANDLER ----------------
    @bot.message_handler(func=lambda m: True)
    def handler(message):
        text = message.text
        chat_id = message.chat.id
        user_id = message.from_user.id

        if chat_id not in spam_speed:
            spam_speed[chat_id] = 2

             # OpenAI translate command ကို ဒီနေရာမှာပဲ ထည့်မယ်
        if text.startswith("ဘာသာပြန်") and message.reply_to_message and is_admin_or_owner(user_id):delete_cmd(message)
        original_text = message.reply_to_message.text

        # Deep Translator
        translated_text = translator.translate(original_text)

        # OpenAI GPT Translation
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role":"user","content":f"Translate this to English concisely:\n{original_text}"}],
                temperature=0.5
            )
            gpt_translation = response.choices[0].message.content
        except Exception as e:
            gpt_translation = f"OpenAI error: {e}"

        bot.send_message(chat_id, f"🌐 DeepTranslator: {translated_text}\n🤖 OpenAI GPT: {gpt_translation}")

        # ---------------- FILTER ----------------
        for word in FILTER_WORDS:
            if word in (text or "").lower() and not is_admin_or_owner(user_id):
                bot.delete_message(chat_id, message.message_id)
                bot.send_message(chat_id, f"{message.from_user.first_name} ဖာသည်မသား")
                return

        if message.entities:
            for ent in message.entities:
                if ent.type in ['url', 'text_link'] and not is_admin_or_owner(user_id):
                    bot.delete_message(chat_id, message.message_id)
                    bot.send_message(chat_id, f"{message.from_user.first_name} မင်းအမေပိုင်တဲ့ဖာရုံမဟုတ်ဘူး")
                    return

        if message.forward_from or message.forward_from_chat:
            if not is_admin_or_owner(user_id):
                bot.delete_message(chat_id, message.message_id)
                bot.send_message(chat_id, f"{message.from_user.first_name} မင်းအမေပိုင်တဲ့ဖာရုံမဟုတ်ဘူး")
                return

        # ---------------- HELP CMD ----------------
        if text == "အကူညီ":
            delete_cmd(message)
            bot.send_message(chat_id, """<pre>
All - member အကုန် call & stop
Callone - တစ်ယောက်ချင်း call & stop
Call - active member call & stop
ရပ် - stop ongoing call
Info - id ကြည့်(reply)
ပိတ်ထား - mute(reply)
လက်မရားနဲ့ - unmute(reply)
လစ် - kick(reply)
ပြန်မလာနဲ့ - ban(reply)
ပြန်ဝင်ခွင့်ပြု - unban(reply)
အက်မင် - gp add_admin(reply)
ရာထူးချ - gp remove_admin(reply)
mtရိုက် - tag spam(reply)
ရိုက်သတ် - spam(reply)
အရှိန် - spam speed
ခွင့်လွှတ်လိုက် - stop spam
ဘာသာပြန် - translate(reply)
filter - auto delete
file - broadcast file
list - bot admin list
ထည့် - add bot admin
ဖြုတ် - remove bot admin
</pre>""")
            return

        # ---------------- LIST ----------------
        if text == "list" and is_admin_or_owner(user_id):
            delete_cmd(message)
            names = [str(uid) for uid in BOT_ADMINS]
            bot.reply_to(message, f"📜 Bot Admins:\nOwner: {OWNER_ID}\nAdmins: {', '.join(names)}")
            return

        # ---------------- FILE BROADCAST ----------------
        if message.content_type == 'document':
            last_doc[chat_id] = message
            bot.reply_to(message, "ဖိုင်ကို စောင့်နေပါတယ်။ Reply 'file' ခေါ်ပြီး broadcast လုပ်ပါ။")
            return

        if text and text.lower() == "file" and is_admin_or_owner(user_id):
            delete_cmd(message)
            if chat_id not in last_doc:
                bot.reply_to(message, "ဖိုင်မတွေ့ပါ။")
                return
            doc_msg = last_doc[chat_id]
            file_info = bot.get_file(doc_msg.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            try:
                text_content = downloaded_file.decode("utf-8")
            except:
                bot.reply_to(message, "ဖတ်၍မရပါ (not a text file).")
                return
            for gp_chat in GP_CHAT_IDS:
                bot.send_message(gp_chat, monobox_message(doc_msg.from_user, text_content))
            bot.reply_to(message, "📤 ဖိုင် broadcast လုပ်ပြီးပါပြီ!")
            del last_doc[chat_id]
            return

        # ---------------- SPEED ----------------
        if text.startswith("အရှိန်") and is_admin_or_owner(user_id):
            delete_cmd(message)
            try:
                speed = int(text.split()[1])
                if 1 <= speed <= 5:
                    spam_speed[chat_id] = speed
                    bot.send_message(chat_id, f"အမြန်နှုံန်း {speed} သတ်မှတ်ပြီးပါပြီ")
            except:
                pass
            return

        # ---------------- STOP SPAM / CALL ----------------
        if text == "ခွင့်လွှတ်လိုက်" and is_admin_or_owner(user_id):
            delete_cmd(message)
            spam_running[chat_id] = False
            call_running[chat_id] = False
            return

        # ---------------- SPAM ----------------
        if text == "mtရိုက်" and message.reply_to_message and is_admin_or_owner(user_id):
            delete_cmd(message)
            user = message.reply_to_message.from_user
            spam_running[chat_id] = True
            def spam_tag():
                while spam_running.get(chat_id):
                    bot.send_message(chat_id, f"<a href='tg://user?id={user.id}'>{user.first_name}</a>\n{SPAM_TEXT}", disable_web_page_preview=True)
                    time.sleep(6 - spam_speed[chat_id])
            threading.Thread(target=spam_tag, daemon=True).start()

        if text == "ရိုက်သတ်" and message.reply_to_message and is_admin_or_owner(user_id):
            delete_cmd(message)
            spam_running[chat_id] = True
            def spam_no_tag():
                while spam_running.get(chat_id):
                    bot.send_message(chat_id, SPAM_TEXT)
                    time.sleep(6 - spam_speed[chat_id])
            threading.Thread(target=spam_tag, daemon=True).start()

        # ---------------- CALL ----------------
        if text == "All" and is_admin_or_owner(user_id):
            delete_cmd(message)
            call_running[chat_id] = True
            for member in bot.get_chat_members(chat_id):
                bot.send_message(chat_id, f"Calling... {member.user.first_name}")
            call_running[chat_id] = False
            return

        if text == "Callone" and is_admin_or_owner(user_id):
            delete_cmd(message)
            call_running[chat_id] = True
            for member in bot.get_chat_members(chat_id):
                bot.send_message(chat_id, f"Calling individually... {member.user.first_name}")
                time.sleep(1)
            call_running[chat_id] = False
            return

        if text == "Call" and is_admin_or_owner(user_id):
            delete_cmd(message)
            call_running[chat_id] = True
            for member in bot.get_chat_members(chat_id):
                if not member.user.is_bot:
                    bot.send_message(chat_id, f"Calling active member... {member.user.first_name}")
            call_running[chat_id] = False
            return

        if text == "ရပ်" and is_admin_or_owner(user_id):
            delete_cmd(message)
            call_running[chat_id] = False
            return

        # ---------------- MUTE / UNMUTE ----------------
        if text == "ပိတ်ထား" and message.reply_to_message and is_admin_or_owner(user_id):
            delete_cmd(message)
            bot.restrict_chat_member(chat_id, message.reply_to_message.from_user.id, ChatPermissions(can_send_messages=False))
            return
        if text == "လက်မရားနဲ့" and message.reply_to_message and is_admin_or_owner(user_id):
            delete_cmd(message)
            bot.restrict_chat_member(chat_id, message.reply_to_message.from_user.id, ChatPermissions(can_send_messages=True))
            return

        # ---------------- KICK / BAN / UNBAN ----------------
        if text == "လစ်" and message.reply_to_message and is_admin_or_owner(user_id):
            delete_cmd(message)
            bot.kick_chat_member(chat_id, message.reply_to_message.from_user.id)
            return
        if text == "ပြန်မလာနဲ့" and message.reply_to_message and is_admin_or_owner(user_id):
            delete_cmd(message)
            bot.ban_chat_member(chat_id, message.reply_to_message.from_user.id)
            return
        if text == "ပြန်ဝင်ခွင့်ပြု" and message.reply_to_message and is_admin_or_owner(user_id):
            delete_cmd(message)
            bot.unban_chat_member(chat_id, message.reply_to_message.from_user.id)
            return

        # ---------------- ADMIN / BOT ADMIN ----------------
        if text == "အက်မင်" and message.reply_to_message and is_admin_or_owner(user_id):
            delete_cmd(message)
            bot.promote_chat_member(chat_id, message.reply_to_message.from_user.id,
                                    can_change_info=True, can_delete_messages=True,
                                    can_invite_users=True, can_pin_messages=True,
                                    can_promote_members=True)
            return
        if text == "ရာထူးချ" and message.reply_to_message and is_admin_or_owner(user_id):
            delete_cmd(message)
            bot.promote_chat_member(chat_id, message.reply_to_message.from_user.id,
                                    can_change_info=False, can_delete_messages=False,
                                    can_invite_users=False, can_pin_messages=False,
                                    can_promote_members=False)
            return
        if text == "ထည့်" and message.reply_to_message and user_id == OWNER_ID:
            delete_cmd(message)
            BOT_ADMINS.append(message.reply_to_message.from_user.id)
            bot.send_message(chat_id, f"{message.reply_to_message.from_user.first_name} သခင့်အမိန့်တော်အတိုင်းနာခံလျှက်ပါ။")
            return
        if text == "ဖြုတ်" and message.reply_to_message and user_id == OWNER_ID:
            delete_cmd(message)
            if message.reply_to_message.from_user.id in BOT_ADMINS:
                BOT_ADMINS.remove(message.reply_to_message.from_user.id)
                bot.send_message(chat_id, f"{message.reply_to_message.from_user.first_name} ကျွန်ုပ်အားဆက်လက်ထိန်းချုပ်ရန်အသင့်မှာစွမ်းရည်မရှိတော့ပါ။")
            return

        # ---------------- INFO ----------------
        if text == "Info" and message.reply_to_message and is_admin_or_owner(user_id):
            delete_cmd(message)
            bot.send_message(chat_id, f"👤 {message.reply_to_message.from_user.first_name}\n🆔 {message.reply_to_message.from_user.id}")

# ---------------- START 4 BOTS ----------------
threads = []
for token in TOKENS:
    t = threading.Thread(target=start_bot, args=(token,))
    t.start()
    threads.append(t)
