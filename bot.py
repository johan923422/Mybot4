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

OWNER_ID = int(os.getenv("OWNER_ID"))
BOT_ADMINS = [987654321, 112233445]
GP_CHAT_IDS = [-1001111111111, -1002222222222, -1003333333333]
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

def is_admin_or_owner(user_id):
    return user_id == OWNER_ID or user_id in BOT_ADMINS

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
            bot.send_message(message.chat.id, f"{user.first_name} ဖာသည်မသားတစ်ကောင်ဝင်လာတယ်\n🆔 ID: {user.id}")

    @bot.message_handler(content_types=['left_chat_member'])
    def goodbye(message):
        user = message.left_chat_member
        bot.send_message(message.chat.id, f"{user.first_name} ဖာသည်မသားတစ်ကောင်ထွက်သွားပြီ\n🆔 ID: {user.id}")

    # ---------------- MAIN HANDLER ----------------
    @bot.message_handler(func=lambda m: True)
    def handler(message):
        text = message.text or ""
        chat_id = message.chat.id
        user_id = message.from_user.id

        if chat_id not in spam_speed:
            spam_speed[chat_id] = 2

        # ---------------- TRANSLATE ----------------
        if text.startswith("ဘာသာပြန်") and message.reply_to_message and is_admin_or_owner(user_id):
            delete_cmd(message)
            original_text = message.reply_to_message.text
            translated_text = translator.translate(original_text)
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role":"user","content":f"Translate this to English concisely:\n{original_text}"}],
                    temperature=0.5
                )
                gpt_translation = response.choices[0].message.content
            except Exception as e:
                gpt_translation = f"OpenAI error: {e}"
            bot.send_message(chat_id, f"🌐 DeepTranslator: {translated_text}\n🤖 GPT: {gpt_translation}")
            return

        # ---------------- FILTER ----------------
        for word in FILTER_WORDS:
            if word in text.lower() and not is_admin_or_owner(user_id):
                bot.delete_message(chat_id, message.message_id)
                bot.send_message(chat_id, f"{message.from_user.first_name} ဖာသည်မသား")
                return

        if message.entities:
            for ent in message.entities:
                if ent.type in ['url','text_link'] and not is_admin_or_owner(user_id):
                    bot.delete_message(chat_id, message.message_id)
                    bot.send_message(chat_id, f"{message.from_user.first_name} မင်းအမေပိုင်တဲ့ဖာရုံမဟုတ်ဘူး")
                    return

        if message.forward_from or message.forward_from_chat:
            if not is_admin_or_owner(user_id):
                bot.delete_message(chat_id, message.message_id)
                bot.send_message(chat_id, f"{message.from_user.first_name} မင်းအမေပိုင်တဲ့ဖာရုံမဟုတ်ဘူး")
                return

        # ---------------- HELP ----------------
        if text == "အကူညီ":
            delete_cmd(message)
            bot.send_message(chat_id, """<pre>
All
Callone
Call
ရပ်
Info
ပိတ်ထား
လက်မရားနဲ့
လစ်
ပြန်မလာနဲ့
ပြန်ဝင်ခွင့်ပြု
အက်မင်
ရာထူးချ
mtရိုက်
ရိုက်သတ်
အရှိန်
ခွင့်လွှတ်လိုက်
ဘာသာပြန်
file
list
ထည့်
ဖြုတ်
</pre>""")
            return

        # ---------------- LIST BOT ADMINS ----------------
        if text == "list" and is_admin_or_owner(user_id):
            delete_cmd(message)
            names = [str(uid) for uid in BOT_ADMINS]
            bot.reply_to(message, f"📜 Bot Admins:\nOwner: {OWNER_ID}\nAdmins: {', '.join(names)}")
            return

        # ---------------- FILE BROADCAST ----------------
        if message.content_type == 'document':
            last_doc[chat_id] = message
            bot.reply_to(message, "Reply 'file' to broadcast.")
            return

        if text.lower() == "file" and is_admin_or_owner(user_id):
            delete_cmd(message)
            if chat_id not in last_doc:
                bot.reply_to(message, "No file found.")
                return
            doc_msg = last_doc[chat_id]
            file_info = bot.get_file(doc_msg.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            try:
                text_content = downloaded_file.decode("utf-8")
            except:
                bot.reply_to(message, "Not a text file.")
                return
            for gp_chat in GP_CHAT_IDS:
                bot.send_message(gp_chat, f"📦 <b>File Broadcast</b>\n👤 From: {doc_msg.from_user.first_name}\n📝 Content:\n<pre>{text_content}</pre>")
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

        # ---------------- SPAM ----------------
        if text in ["mtရိုက်","ရိုက်သတ်"] and message.reply_to_message and is_admin_or_owner(user_id):
            delete_cmd(message)
            user = message.reply_to_message.from_user
            spam_running[chat_id] = True

            def spam_worker(tag_user: bool):
                while spam_running.get(chat_id):
                    if tag_user:
                        bot.send_message(chat_id, f"<a href='tg://user?id={user.id}'>{user.first_name}</a>\n{SPAM_TEXT}", disable_web_page_preview=True)
                    else:
                        bot.send_message(chat_id, SPAM_TEXT)
                    time.sleep(6 - spam_speed[chat_id])
            threading.Thread(target=spam_worker, args=(text=="mtရိုက်",), daemon=True).start()
            return

        # ---------------- STOP SPAM ----------------
        if text == "ခွင့်လွှတ်လိုက်" and is_admin_or_owner(user_id):
            delete_cmd(message)
            spam_running[chat_id] = False
            bot.send_message(chat_id, "🛑 Spam ရပ်လိုက်ပါပြီ")
            return

        # ---------------- CALL LOGIC (optimized) ----------------
        if text in ["All","Callone","Call"] and is_admin_or_owner(user_id):
            delete_cmd(message)
            call_running[chat_id] = True
            try:
                admins = bot.get_chat_administrators(chat_id)
                if text == "All":
                    for m in admins:
                        bot.send_message(chat_id, f"Calling... {m.user.first_name}")
                elif text == "Callone":
                    for m in admins:
                        bot.send_message(chat_id, f"Calling individually... {m.user.first_name}")
                        time.sleep(1)
                elif text == "Call":
                    for m in admins:
                        if not m.user.is_bot:
                            bot.send_message(chat_id, f"Calling active member... {m.user.first_name}")
            except:
                pass
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
            return
        if text == "ဖြုတ်" and message.reply_to_message and user_id == OWNER_ID:
            delete_cmd(message)
            if message.reply_to_message.from_user.id in BOT_ADMINS:
                BOT_ADMINS.remove(message.reply_to_message.from_user.id)
            return

        # ---------------- INFO ----------------
        if text == "Info" and message.reply_to_message and is_admin_or_owner(user_id):
            delete_cmd(message)
            bot.send_message(chat_id, f"👤 {message.reply_to_message.from_user.first_name}\n🆔 {message.reply_to_message.from_user.id}")
            return

    # ---------------- START BOT ----------------
    bot.infinity_polling(skip_pending=True)

# ---------------- RUN ALL BOTS ----------------
threads = []
for token in TOKENS:
    if token:
        t = threading.Thread(target=start_bot, args=(token,))
        t.start()
        threads.append(t)

# ---------------- KEEP SCRIPT RUNNING FOR RAILWAY ----------------
while True:
    time.sleep(10)
