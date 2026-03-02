import os
import asyncio
import json
from pyrogram import Client, filters
from pyrogram.types import ChatPermissions, Message
from pyrogram.enums import ParseMode
from deep_translator import GoogleTranslator

# ---------------- CONFIG ----------------
TOKENS = [os.getenv("BOT1"), os.getenv("BOT2"), os.getenv("BOT3"), os.getenv("BOT4")]
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
OWNER_ID = int(os.getenv("OWNER_ID"))

GP_CHAT_IDS = [-1001111111111, -1002222222222, -1003333333333]
FILTER_WORDS = ["badword1", "badword2"]

translator = GoogleTranslator(source='auto', target='my')
DATA_FILE = "data.json"

# ---------------- GLOBAL STATE ----------------
spam_speed = {}
spam_running = {}
call_running = {}
last_doc = {}

# ---------------- HELPER FUNCTIONS ----------------
def is_admin_or_owner(user_id: int, admins: list):
    return user_id == OWNER_ID or user_id in admins

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return {"SPAM_TEXT": [
            "ဘာပုတယ်ညာပုတယ်နဲ့ဉာဏ်ရည်ကမမှီဘူး",
            "မင်းဉာဏ်ရည်နဲ့ကျမ်းတိုက်ဖုန်သုပ်တောင်ရမယ့်ကောင်မဟုတ်ဘူး",
            "ကြောက်လို့လက်တုန်နေပြီလား",
            "ညီပုပြေးတော့မလို့လား",
            "မင်းအဆင့်လောက်နဲ့ငါကို ယှဉ်နိုင်မှာလဲမဟုတ်ပါဘူး",
            "ခွေးလေးကိုက်စမ်း",
            "မင်းအမေကဖာသည်မကြီးဆို",
            "ဘာလဲမင်းအမေကိုငါမလိုးပေးလို့လောင်တာလား",
            "စောက်ခြောက်လိုလုပ်မနေနဲ့ကြာတယ်",
            "ကိုက်စမ်းဖာပြက်မသား"
        ], "BOT_ADMINS": [987654321, 112233445], "spam_speed": {}}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ---------------- CALL FUNCTION ----------------
async def call_members_online(client, message: Message, mode: str, optional_text: str = ""):
    chat_id = message.chat.id
    user_id = message.from_user.id
    data = load_data()
    if not is_admin_or_owner(user_id, data["BOT_ADMINS"]):
        return

    await message.delete()
    call_running[chat_id] = True
    members = []

    if mode == "Callone":
        async for m in client.get_chat_members(chat_id, filter="administrators"):
            members.append(m)
    elif mode == "All":
        async for m in client.get_chat_members(chat_id):
            members.append(m)
    elif mode == "Call":
        async for m in client.get_chat_members(chat_id):
            if m.user and not m.user.is_bot:
                members.append(m)

    mention_list = [
        f"<a href='tg://user?id={m.user.id}'>{m.user.first_name}</a>"
        for m in members if m.user
    ]

    batch_size = 7
    for i in range(0, len(mention_list), batch_size):
        if not call_running.get(chat_id):
            break
        batch = mention_list[i:i+batch_size]
        msg_text = optional_text + "\n" + "\n".join(batch) if optional_text else "\n".join(batch)
        await client.send_message(chat_id, msg_text, parse_mode=ParseMode.HTML)
        await asyncio.sleep(1)

    call_running[chat_id] = False

# ---------------- BOT ----------------
async def run_bot(token: str):
    data = load_data()
    app = Client(name=f"bot_{token[:5]}", api_id=API_ID, api_hash=API_HASH, bot_token=token)

    # -------- Welcome --------
    @app.on_message(filters.new_chat_members)
    async def welcome(client, message: Message):
        for user in message.new_chat_members:
            mention = f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"
            try:
                photo = await client.download_media(user.photo.big_file_id)
                await client.send_photo(message.chat.id, photo, caption=f"{mention} ဖာသည်မသားဝင်လာပြီ\n🆔 {user.id}")
            except:
                await message.reply_text(f"{mention} ဖာသည်မသားဝင်လာပြီ\n🆔 {user.id}")

    # -------- Goodbye --------
    @app.on_message(filters.left_chat_member)
    async def goodbye(client, message: Message):
        user = message.left_chat_member
        mention = f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"
        try:
            photo = await client.download_media(user.photo.big_file_id)
            await client.send_photo(message.chat.id, photo, caption=f"{mention} ဖာသည်မသားထွက်သွားပြီ\n🆔 {user.id}")
        except:
            await message.reply_text(f"{mention} ဖာသည်မသားထွက်သွားပြီ\n🆔 {user.id}")

    @app.on_message(filters.text)
    async def handler(client, message: Message):
        nonlocal data
        text = message.text or ""
        chat_id = message.chat.id
        user_id = message.from_user.id

        if chat_id not in data["spam_speed"]:
            data["spam_speed"][chat_id] = 2

        # -------- CALL CMDS --------
        if text.startswith("All"):
            await call_members_online(client, message, "All", text[3:].strip())
            return
        if text.startswith("Callone"):
            await call_members_online(client, message, "Callone", text[7:].strip())
            return
        if text.startswith("Call"):
            await call_members_online(client, message, "Call", text[4:].strip())
            return
        if text == "ရပ်":
            await message.delete()
            call_running[chat_id] = False
            await message.reply_text("Call ရပ်ပြီးပါပြီသခင်")
            return

        # -------- SPAM CMDS --------
        if text in ["mtရိုက်","ရိုက်သတ်"] and message.reply_to_message and is_admin_or_owner(user_id, data["BOT_ADMINS"]):
            await message.delete()
            user = message.reply_to_message.from_user
            spam_running[chat_id] = True

            async def spam_worker(tag_user: bool):
                while spam_running.get(chat_id):
                    for line in data["SPAM_TEXT"]:
                        if not spam_running.get(chat_id):
                            break
                        if tag_user:
                            await app.send_message(chat_id, f"<a href='tg://user?id={user.id}'>{user.first_name}</a>\n{line}", parse_mode=ParseMode.HTML)
                        else:
                            await app.send_message(chat_id, line)
                        await asyncio.sleep(6 - data["spam_speed"][chat_id])

            asyncio.create_task(spam_worker(tag_user=text=="mtရိုက်"))
            return

        if text == "ခွင့်လွှတ်လိုက်" and is_admin_or_owner(user_id, data["BOT_ADMINS"]):
            await message.delete()
            spam_running[chat_id] = False
            await message.reply_text("သခင့်အမိန့်အရဖာသည်မသားကိုလွတ်မြောက်ခွင့်ပေးလိုက်ပါပြီ")
            return

        # -------- SPAM TEXT MANAGER --------
        if text.startswith("စာထည့်") and is_admin_or_owner(user_id, data["BOT_ADMINS"]):
            await message.delete()
            new_text = text.replace("စာထည့်","",1).strip()
            if new_text:
                data["SPAM_TEXT"].append(new_text)
                save_data(data)
                await message.reply_text(f"ထည့်ပြီးပါပြီ:\n{new_text}")
            return

        if text == "စာlist" and is_admin_or_owner(user_id, data["BOT_ADMINS"]):
            await message.delete()
            msg = "\n".join([f"{i+1}. {line}" for i,line in enumerate(data["SPAM_TEXT"])])
            await message.reply_text(f"<pre>{msg}</pre>", parse_mode=ParseMode.HTML)
            return

        if text.startswith("စာဖြတ်") and is_admin_or_owner(user_id, data["BOT_ADMINS"]):
            await message.delete()
            remove_text = text.replace("စာဖြတ်","",1).strip()
            if remove_text in data["SPAM_TEXT"]:
                data["SPAM_TEXT"].remove(remove_text)
                save_data(data)
                await message.reply_text(f"ဖြတ်ပြီးပါပြီ:\n{remove_text}")
            else:
                await message.reply_text("မတွေ့ပါ။")
            return

        # -------- SPEED --------
        if text.startswith("အရှိန်") and is_admin_or_owner(user_id, data["BOT_ADMINS"]):
            await message.delete()
            try:
                speed = int(text.split()[1])
                if 1 <= speed <= 5:
                    data["spam_speed"][chat_id] = speed
                    save_data(data)
                    await message.reply_text(f"အမြန်နှုန်း {speed} သတ်မှတ်ပြီးပါပြီ")
            except:
                await message.reply_text("1-5 သာသုံးပါ။")
            return

        # -------- TRANSLATE --------
        if text.startswith("ဘာသာပြန်") and message.reply_to_message and is_admin_or_owner(user_id, data["BOT_ADMINS"]):
            await message.delete()
            original_text = message.reply_to_message.text
            translated_text = translator.translate(original_text)
            await message.reply_text(f"🌐 {translated_text}")
            return

        # -------- FILTER --------
        for word in FILTER_WORDS:
            if word in text.lower() and not is_admin_or_owner(user_id, data["BOT_ADMINS"]):
                await message.delete()
                await message.reply_text(f"{message.from_user.first_name} ဖာသည်မသား")
                return

        if message.entities:
            for ent in message.entities:
                if ent.type in ['url','text_link'] and not is_admin_or_owner(user_id, data["BOT_ADMINS"]):
                    await message.delete()
                    await message.reply_text(f"{message.from_user.first_name} မင်းအမေပိုင်တဲ့ဖာရုံမဟုတ်ဘူး")
                    return

        if message.forward_from or message.forward_from_chat:
            if not is_admin_or_owner(user_id, data["BOT_ADMINS"]):
                await message.delete()
                await message.reply_text(f"{message.from_user.first_name} မင်းအမေပိုင်တဲ့ဖာရုံမဟုတ်ဘူး")
                return

        # -------- HELP --------
        if text == "အကူညီ":
            await message.delete()
            await message.reply_text("""<pre>
All - Call all member
Callone - Call all admin
Call - Call all active member
ရပ် - stop call
Info - show user id(reply)
ပိတ်ထား - mute(reply)
လက်မရားနဲ့ - unmute(reply)
ပြန်မလာနဲ့ - ban(reply)
ပြန်ဝင်ခွင့်ပြု - unban(reply)
mtရိုက် - tag spam(reply)
ရိုက်သတ် - normal spam(reply)
အရှိန် - spam speed(1 - 5)
ခွင့်လွှတ်လိုက် - stop all spam
ဘာသာပြန် - translate
file - Broadcast

Bot need all permission to use admin cmd in gp.
Creator - @Legendary_Johan_Sama
Channel - @Johan_132IQ
Need permission to use Bot's cmd.
I don't wanna argue i'm a beginner, making bot just for fun.
</pre>""", parse_mode=ParseMode.HTML)
            return

        # -------- LIST ADMINS --------
        if text == "list" and is_admin_or_owner(user_id, data["BOT_ADMINS"]):
            await message.delete()
            names = [str(uid) for uid in data["BOT_ADMINS"]]
            await message.reply_text(f"📜 Bot Admins:\nOwner: {OWNER_ID}\nAdmins: {', '.join(names)}")
            return

        # -------- FILE BROADCAST --------
        if text.lower() == "file" and message.reply_to_message and is_admin_or_owner(user_id, data["BOT_ADMINS"]):
            await message.delete()
            content = message.reply_to_message.text
            for gp in GP_CHAT_IDS:
                await app.send_message(gp, f"<pre>{content}</pre>", parse_mode=ParseMode.HTML)
            return

        # -------- ADMIN CMDS --------
        if text == "ပိတ်ထား" and message.reply_to_message and is_admin_or_owner(user_id, data["BOT_ADMINS"]):
            await message.delete()
            await app.restrict_chat_member(chat_id, message.reply_to_message.from_user.id, ChatPermissions(can_send_messages=False))
            return

        if text == "လက်မရားနဲ့" and message.reply_to_message and is_admin_or_owner(user_id, data["BOT_ADMINS"]):
            await message.delete()
            await app.restrict_chat_member(chat_id, message.reply_to_message.from_user.id, ChatPermissions(can_send_messages=True))
            return

        if text == "ပြန်မလာနဲ့" and message.reply_to_message and is_admin_or_owner(user_id, data["BOT_ADMINS"]):
            await message.delete()
            await app.ban_chat_member(chat_id, message.reply_to_message.from_user.id)
            return

        if text == "ပြန်ဝင်ခွင့်ပြု" and message.reply_to_message and is_admin_or_owner(user_id, data["BOT_ADMINS"]):
            await message.delete()
            await app.unban_chat_member(chat_id, message.reply_to_message.from_user.id)
            return

        if text == "ထည့်" and message.reply_to_message and user_id == OWNER_ID:
            await message.delete()
            data["BOT_ADMINS"].append(message.reply_to_message.from_user.id)
            save_data(data)
            return

        if text == "ဖြုတ်" and message.reply_to_message and user_id == OWNER_ID:
            await message.delete()
            if message.reply_to_message.from_user.id in data["BOT_ADMINS"]:
                data["BOT_ADMINS"].remove(message.reply_to_message.from_user.id)
                save_data(data)
            return

        if text == "Info" and message.reply_to_message and is_admin_or_owner(user_id, data["BOT_ADMINS"]):
            await message.delete()
            await message.reply_text(f"👤 {message.reply_to_message.from_user.first_name}\n🆔 {message.reply_to_message.from_user.id}")
            return

    await app.start()
    print(f"Bot started: {token}")
    await asyncio.Event().wait()

# ---------------- RUN ALL ----------------
async def main():
    await asyncio.gather(*(run_bot(token) for token in TOKENS if token))

asyncio.run(main())
