import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import ChatPermissions, Message
import openai
from deep_translator import GoogleTranslator

# ---------------- CONFIG ----------------
TOKENS = [os.getenv("BOT1"), os.getenv("BOT2"), os.getenv("BOT3"), os.getenv("BOT4")]
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
OPENAI_KEY = os.getenv("OPENAI_KEY")
openai.api_key = OPENAI_KEY
OWNER_ID = int(os.getenv("OWNER_ID"))
BOT_ADMINS = [987654321, 112233445]
GP_CHAT_IDS = [-1001111111111, -1002222222222, -1003333333333]
FILTER_WORDS = ["badword1","badword2"]
translator = GoogleTranslator(source='auto', target='my')

# ---------------- GLOBAL STATE ----------------
spam_speed = {}
spam_running = {}
call_running = {}
last_doc = {}
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

# ---------------- HELPERS ----------------
def is_admin_or_owner(user_id: int):
    return user_id == OWNER_ID or user_id in BOT_ADMINS

# ---------------- CALL FUNCTION ----------------
async def call_members_online(client, message: Message, mode: str, optional_text: str = ""):
    chat_id = message.chat.id
    user_id = message.from_user.id
    if not is_admin_or_owner(user_id):
        return
    await message.delete()
    call_running[chat_id] = True

    try:
        members = []
        if mode == "Callone":
            members = []
async for m in client.get_chat_members(chat_id, filter="administrators"):
    members.append(m)
        elif mode == "All":
            members = []
async for m in client.get_chat_members(chat_id):
    members.append(m)
        elif mode == "Call":
            async for m in client.get_chat_members(chat_id):
                if m.user and not m.user.is_bot:
                    status = getattr(m.user, "status", "")
                    if status in ["online","recently"]:
                        members.append(m)

        mention_list = []
        for m in members:
            if not call_running.get(chat_id):
                break
            user_obj = m.user if hasattr(m,"user") else m
            mention_list.append(f"<a href='tg://user?id={user_obj.id}'>{user_obj.first_name}</a>")

        batch_size = 7
        for i in range(0, len(mention_list), batch_size):
            if not call_running.get(chat_id):
                break
            batch = mention_list[i:i+batch_size]
            msg_text = optional_text + "\n" + "\n".join(batch) if optional_text else "\n".join(batch)
            await client.send_message(chat_id, msg_text, disable_web_page_preview=True)
            await asyncio.sleep(1)
    except Exception as e:
        await client.send_message(chat_id, f"Call error: {e}")

    call_running[chat_id] = False

# ---------------- BOT LOGIC ----------------
async def run_bot(token: str):
    app = Client(name=f"bot_{token[:5]}",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=token
                )

    # --- Welcome / Goodbye ---
    @app.on_message(filters.new_chat_members)
    async def welcome(client, message: Message):
        for user in message.new_chat_members:
            await message.reply_text(f"{user.first_name} ဖာသည်မသားဝင်လာပြီ\n🆔 {user.id}")

    @app.on_message(filters.left_chat_member)
    async def goodbye(client, message: Message):
        user = message.left_chat_member
        await message.reply_text(f"{user.first_name} ဖာသည်မသားထွက်သွားပြီ\n🆔 {user.id}")

    # --- Main handler ---
    @app.on_message(filters.text)
    async def handler(client, message: Message):
        text = message.text or ""
        chat_id = message.chat.id
        user_id = message.from_user.id

        if chat_id not in spam_speed:
            spam_speed[chat_id] = 2

        # --- Call commands ---
        if text.startswith("All"):
            optional_text = text[3:].strip()
            await call_members_online(client, message, mode="All", optional_text=optional_text)
            return
        if text.startswith("Callone"):
            optional_text = text[7:].strip()
            await call_members_online(client, message, mode="Callone", optional_text=optional_text)
            return
        if text.startswith("Call"):
            optional_text = text[4:].strip()
            await call_members_online(client, message, mode="Call", optional_text=optional_text)
            return
        if text == "ရပ်":
            await message.delete()
            call_running[chat_id] = False
            await message.reply_text("Call ရပ်ပြီးပါပြီသခင်")
            return

        # --- Spam ---
        if text in ["mtရိုက်","ရိုက်သတ်"] and message.reply_to_message and is_admin_or_owner(user_id):
            await message.delete()
            user = message.reply_to_message.from_user
            spam_running[chat_id] = True
            async def spam_worker(tag_user: bool):
                while spam_running.get(chat_id):
                    if tag_user:
                        await app.send_message(chat_id, f"<a href='tg://user?id={user.id}'>{user.first_name}</a>\n{SPAM_TEXT}", disable_web_page_preview=True)
                    else:
                        await app.send_message(chat_id, SPAM_TEXT)
                    await asyncio.sleep(6 - spam_speed[chat_id])
            asyncio.create_task(spam_worker(tag_user=text=="mtရိုက်"))
            return
        if text == "ခွင့်လွှတ်လိုက်" and is_admin_or_owner(user_id):
            await message.delete()
            spam_running[chat_id] = False
            await message.reply_text("သခင့်အမိန့်အရဖာသည်မသားကိုလွတ်မြောက်ခွင့်ပေးလိုက်ပါပြီ")
            return

        # --- Speed command (အရှိန်) ---
        if text.startswith("အရှိန်") and is_admin_or_owner(user_id):
            await message.delete()
            try:
                speed = int(text.split()[1])
                if 1 <= speed <= 5:
                    spam_speed[chat_id] = speed
                    await message.reply_text(f"အမြန်နှုန်း {speed} သတ်မှတ်ပြီးပါပြီ")
            except:
                await message.reply_text("အမှားရှိပါတယ်၊ 1-5 အတွင်းနံပါတ်သာအသုံးပြုပါ။")
            return

        # --- Translate ---
        if text.startswith("ဘာသာပြန်") and message.reply_to_message and is_admin_or_owner(user_id):
            await message.delete()
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
            await message.reply_text(f"🌐 DeepTranslator: {translated_text}\n🤖 GPT: {gpt_translation}")
            return

        # --- Filter ---
        for word in FILTER_WORDS:
            if word in text.lower() and not is_admin_or_owner(user_id):
                await message.delete()
                await message.reply_text(f"{message.from_user.first_name} ဖာသည်မသား")
                return
        if message.entities:
            for ent in message.entities:
                if ent.type in ['url','text_link'] and not is_admin_or_owner(user_id):
                    await message.delete()
                    await message.reply_text(f"{message.from_user.first_name} မင်းအမေပိုင်တဲ့ဖာရုံမဟုတ်ဘူး")
                    return
        if message.forward_from or message.forward_from_chat:
            if not is_admin_or_owner(user_id):
                await message.delete()
                await message.reply_text(f"{message.from_user.first_name} မင်းအမေပိုင်တဲ့ဖာရုံမဟုတ်ဘူး")
                return

        # --- Help ---
        if text == "အကူညီ":
            await message.delete()
            await message.reply_text("""<pre>
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

        # --- List admins ---
        if text == "list" and is_admin_or_owner(user_id):
            await message.delete()
            names = [str(uid) for uid in BOT_ADMINS]
            await message.reply_text(f"📜 Bot Admins:\nOwner: {OWNER_ID}\nAdmins: {', '.join(names)}")
            return

        # --- File broadcast ---
        if message.document:
            last_doc[chat_id] = message
            await message.reply_text("Reply 'file' to broadcast.")
            return
        if text.lower() == "file" and is_admin_or_owner(user_id):
            await message.delete()
            if chat_id not in last_doc:
                await message.reply_text("No file found.")
                return
            doc_msg = last_doc[chat_id]
            file_info = await app.get_messages(doc_msg.chat.id, doc_msg.message_id)
            downloaded_file = await app.download_media(file_info)
            try:
                text_content = downloaded_file.decode("utf-8")
            except:
                await message.reply_text("Not a text file.")
                return
            for gp_chat in GP_CHAT_IDS:
                await app.send_message(gp_chat, f"📦 <b>File Broadcast</b>\n👤 From: {doc_msg.from_user.first_name}\n📝 Content:\n<pre>{text_content}</pre>")
            del last_doc[chat_id]
            return

        # --- Admin commands ---
        # Mute/Unmute
        if text == "ပိတ်ထား" and message.reply_to_message and is_admin_or_owner(user_id):
            await message.delete()
            await app.restrict_chat_member(chat_id, message.reply_to_message.from_user.id, ChatPermissions(can_send_messages=False))
            return
        if text == "လက်မရားနဲ့" and message.reply_to_message and is_admin_or_owner(user_id):
            await message.delete()
            await app.restrict_chat_member(chat_id, message.reply_to_message.from_user.id, ChatPermissions(can_send_messages=True))
            return
        # Kick/Ban/Unban
        if text == "လစ်" and message.reply_to_message and is_admin_or_owner(user_id):
            await message.delete()
            await app.kick_chat_member(chat_id, message.reply_to_message.from_user.id)
            return
        if text == "ပြန်မလာနဲ့" and message.reply_to_message and is_admin_or_owner(user_id):
            await message.delete()
            await app.ban_chat_member(chat_id, message.reply_to_message.from_user.id)
            return
        if text == "ပြန်ဝင်ခွင့်ပြု" and message.reply_to_message and is_admin_or_owner(user_id):
            await message.delete()
            await app.unban_chat_member(chat_id, message.reply_to_message.from_user.id)
            return
        # Promote/Demote/Bot admins
        if text == "အက်မင်" and message.reply_to_message and is_admin_or_owner(user_id):
            await message.delete()
            await app.promote_chat_member(chat_id, message.reply_to_message.from_user.id,
                                          can_change_info=True, can_delete_messages=True,
                                          can_invite_users=True, can_pin_messages=True,
                                          can_promote_members=True)
            return
        if text == "ရာထူးချ" and message.reply_to_message and is_admin_or_owner(user_id):
            await message.delete()
            await app.promote_chat_member(chat_id, message.reply_to_message.from_user.id,
                                          can_change_info=False, can_delete_messages=False,
                                          can_invite_users=False, can_pin_messages=False,
                                          can_promote_members=False)
            return
        if text == "ထည့်" and message.reply_to_message and user_id == OWNER_ID:
            await message.delete()
            BOT_ADMINS.append(message.reply_to_message.from_user.id)
            return
        if text == "ဖြုတ်" and message.reply_to_message and user_id == OWNER_ID:
            await message.delete()
            if message.reply_to_message.from_user.id in BOT_ADMINS:
                BOT_ADMINS.remove(message.reply_to_message.from_user.id)
            return
        # Info
        if text == "Info" and message.reply_to_message and is_admin_or_owner(user_id):
            await message.delete()
            await message.reply_text(f"👤 {message.reply_to_message.from_user.first_name}\n🆔 {message.reply_to_message.from_user.id}")
            return

    await app.start()
    print(f"Bot started: {token}")
    await app.idle()

# ---------------- RUN ALL BOTS ----------------
async def main():
    await asyncio.gather(*(run_bot(token) for token in TOKENS if token))

asyncio.run(main())
