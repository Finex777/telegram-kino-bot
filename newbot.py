from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import sqlite3

# ==========================
# 1️⃣ BOT SOZLAMALARI
TOKEN = "8536819940:AAH7lDPwt4vn7hjaKV_GIOL8UxuyLQHPzgA"
ADMIN_ID = 8411962922  # Telegram ID
CHANNEL = "@Mutlfilim_Kinolar"  # Siz yaratgan kanal username
# ==========================

# ==========================
# 2️⃣ BOT VA STORAGE
storage = MemoryStorage()
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=storage)
# ==========================

# ==========================
# 3️⃣ MA'LUMOTLAR BAZASI
db = sqlite3.connect("kino.db")
sql = db.cursor()
sql.execute("""
CREATE TABLE IF NOT EXISTS kino (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE,
    title TEXT,
    file_id TEXT
)
""")
db.commit()
# ==========================

# ==========================
# 4️⃣ START MESSAGE
@dp.message_handler(commands=['start'])
async def start(msg: types.Message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📚 Kino ro'yxati", "🎬 Kino qo'shish (Admin)")
    await msg.answer("🎥 Kino botga xush kelibsiz!", reply_markup=markup)
# ==========================

# ==========================
# 5️⃣ INLINE KINO RO'YXATI
@dp.message_handler(lambda m: m.text == "📚 Kino ro'yxati")
async def show_kino(msg: types.Message):
    sql.execute("SELECT code, title FROM kino")
    rows = sql.fetchall()
    if not rows:
        await msg.answer("📭 Hozircha kino mavjud emas")
        return

    markup = types.InlineKeyboardMarkup(row_width=2)
    for code, title in rows:
        markup.add(types.InlineKeyboardButton(f"{title} ({code})", callback_data=f"kod_{code}"))
    # Kanal linki inline tugma sifatida qo'shish
    markup.add(types.InlineKeyboardButton("📌 Kanalga kirish", url=f"https://t.me/{CHANNEL.replace('@','')}"))
    await msg.answer("🎬 Kino ro'yxati:", reply_markup=markup)

@dp.callback_query_handler(lambda c: c.data.startswith("kod_"))
async def send_kino(call: types.CallbackQuery):
    code = call.data.replace("kod_", "")
    sql.execute("SELECT file_id FROM kino WHERE code=?", (code,))
    row = sql.fetchone()
    if row:
        await bot.send_video(call.message.chat.id, row[0])
    else:
        await call.message.answer("❌ Kino topilmadi")
# ==========================

# ==========================
# 6️⃣ ADMIN KINO QO'SHISH
@dp.message_handler(lambda m: m.text == "🎬 Kino qo'shish (Admin)")
async def admin_add(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        await msg.answer("❌ Siz admin emassiz")
        return
    await msg.answer("📩 Videoni yuboring")
    await dp.current_state(user=msg.from_user.id).set_state("WAIT_VIDEO")

@dp.message_handler(content_types=types.ContentType.VIDEO, state="WAIT_VIDEO")
async def get_video(msg: types.Message):
    await dp.current_state(user=msg.from_user.id).update_data(file_id=msg.video.file_id)
    await msg.answer("🔑 Kino kodi (masalan: 101) ni yozing")
    await dp.current_state(user=msg.from_user.id).set_state("WAIT_CODE")

@dp.message_handler(lambda m: True, state="WAIT_CODE")
async def get_code(msg: types.Message):
    data = await dp.current_state(user=msg.from_user.id).get_data()
    file_id = data.get("file_id")
    code = msg.text
    sql.execute("INSERT OR REPLACE INTO kino (code, title, file_id) VALUES (?,?,?)",
                (code, f"Kino {code}", file_id))
    db.commit()
    await msg.answer(f"✅ Kino saqlandi. Kod: {code}")
    await dp.current_state(user=msg.from_user.id).finish()
# ==========================

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
    
