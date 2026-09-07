import asyncio
import logging
import os
import aiohttp
import aiosqlite
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

BOT_TOKEN = "8634088211:AAET10Uduaz3Z2myTvRM4WMn79WoSVNa35k"
COC_API_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0aW1lc3RhbXAiOjE3MjU2M2M2MjY2NSJ9.eyJpc3MiOiJzdXBlcmNlbGwiLCJhdWQiOiJzdXBlcmNlbGwiLCJmcm9tU2VydmljZSI6InpldXMiLCJkZXNjcmlwdGlvbiI6InYyI1M2MjhmLTRkZGE1ZTcwOWFjTNdUONiwic3ViIjoicGV2ZWxvcGVyLzhmNjcXNzLLWQ0ZjktNDAxZZi05NTgxLTNhMzc3TgzMjdkMiIsInNjb3BlcyI6WyJjb2Fzc2JdLcJsaw1pdHMiT0ltNInRpZXJzIjoiJkZXZlb3A2ZXI2ZSIwZWlsZS1lnRocm9dGxpb21c1fSx7ImNpZHJzIjpbIjI0LjU3LjEiLCIyMTYuMjQuNTcuMiJdLCJ0ZXJtcyI6IHNjX0EXBLIjoiY2xpcZW5OIn1dfQ.6WKwTFcHHfSa3tDdhEU8Blw9vGXBwo1YvxMCtyiaOyUQK5gTOAwa94219d5q-znQgiKviKXWiKuCnXUPeJyyhQ"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class SellAccountState(StatesGroup):
    waiting_for_tag = State()
    waiting_for_price = State()

class CheckTagState(StatesGroup):
    waiting_for_tag = State()

async def init_db():
    async with aiosqlite.connect('clash_bot.db') as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                seller_id INTEGER,
                seller_username TEXT,
                tag TEXT,
                name TEXT,
                th_level INTEGER,
                trophies INTEGER,
                price TEXT,
                status TEXT DEFAULT 'AVAILABLE'
            )
        ''')
        await db.commit()

def main_reply_keyboard():
    kb = [
        [KeyboardButton(text="🛒 سوق الحسابات"), KeyboardButton(text="➕ عرض حساب للبيع")],
        [KeyboardButton(text="🔍 فحص قرية تلقائياً"), KeyboardButton(text="🛡️ نظام الوساطة والضمان")],
        [KeyboardButton(text="👤 حسابي والدعم")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

async def get_player_data(tag: str):
    clean_tag = tag.strip().upper().replace("#", "%23")
    if not clean_tag.startswith("%23"):
        clean_tag = "%23" + clean_tag

    url = f"https://api.clashofclans.com/v1/players/{clean_tag}"
    headers = {
        "Authorization": f"Bearer {COC_API_TOKEN}",
        "Accept": "application/json"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=10) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    logging.error(f"CoC API Error Code: {resp.status}")
                    return None
    except Exception as e:
        logging.error(f"Network error CoC API: {e}")
        return None

@dp.message(CommandStart())
async def start_cmd(msg: types.Message, state: FSMContext):
    await state.clear()
    welcome_msg = (
        f"👋 أهلاً بك يا **{msg.from_user.first_name}** في بوت الوساطة وسوق حسابات كلاش أوف كلانس!\n\n"
        "استخدم الأزرار في الشريط السفلي للتنقل والتحكم في الخدمات بسهولة."
    )
    await msg.answer(welcome_msg, parse_mode="Markdown", reply_markup=main_reply_keyboard())

@dp.message(F.text == "🔍 فحص قرية تلقائياً")
async def check_tag_start(msg: types.Message, state: FSMContext):
    await state.set_state(CheckTagState.waiting_for_tag)
    await msg.answer("📝 أرسل الآن الهاشتاق (Tag) الخاص بالقرية (مثال: `#2PP0LP8Y`):", reply_markup=main_reply_keyboard())

@dp.message(CheckTagState.waiting_for_tag)
async def process_tag_check(msg: types.Message, state: FSMContext):
    tag = msg.text.strip()
    await msg.answer("🔍 جاري جلب التفاصيل الرسمية من Supercell...")
    
    data = await get_player_data(tag)
    if data:
        heroes = "\n".join([f"• {h['name']}: مستوى {h['level']}" for h in data.get('heroes', [])])
        text = (
            f"🏰 **تفاصيل القرية الموثقة:**\n\n"
            f"👤 **الاسم:** {data.get('name')}\n"
            f"🏷️ **الـ Tag:** `{data.get('tag')}`\n"
            f"🏛️ **تاون هول (TH):** {data.get('townHallLevel')}\n"
            f"🏆 **الكؤوس:** {data.get('trophies')}\n"
            f"⚔️ **مستويات الأبطال:**\n{heroes if heroes else 'لا يوجد أبطال'}"
        )
        await msg.answer(text, parse_mode="Markdown")
    else:
        await msg.answer("❌ تعذر جلب البيانات تقنياً. تأكد من إرسال الـ Tag الصحيح.")
    
    await state.clear()

@dp.message(F.text == "🛡️ نظام الوساطة والضمان")
async def escrow_info(msg: types.Message):
    info_text = (
        "🛡️ **كيف يتم تحويل وتأمين الأموال عبر نظام الوساطة؟**\n\n"
        "1️⃣ **الاتفاق:** يتفق المشتري والبائع عبر البوت على السعر والحساب.\n"
        "2️⃣ **الإيداع:** يقوم المشتري بتسليم المبلغ للبوت ليكون تحت الضمان.\n"
        "3️⃣ **التسليم:** يزود البائع المشتري ببيانات Supercell ID.\n"
        "4️⃣ **التأكيد:** بعد فحص المشتري للحساب وتغيير البريد الإلكتروني، يضغط على تأكيد الاستلام ليتم تحويل المال للبائع فوراً."
    )
    await msg.answer(info_text, parse_mode="Markdown")

@dp.message(F.text == "➕ عرض حساب للبيع")
async def sell_start(msg: types.Message, state: FSMContext):
    await state.set_state(SellAccountState.waiting_for_tag)
    await msg.answer("📝 أدخل الهاشتاق (Tag) للقرية المراد عرضها للبيع (مثال: `#2PP0LP8Y`):")

@dp.message(SellAccountState.waiting_for_tag)
async def sell_tag(msg: types.Message, state: FSMContext):
    tag = msg.text.strip()
    await msg.answer("🔍 جاري الفحص والتأكد من وجود القرية في السيرفرات الرسمية...")
    data = await get_player_data(tag)
    
    if data:
        await state.update_data(
            tag=data.get('tag'),
            name=data.get('name'),
            th=data.get('townHallLevel'),
            trophies=data.get('trophies')
        )
        await state.set_state(SellAccountState.waiting_for_price)
        await msg.answer(
            f"✅ **تم التحقق بنجاح من القرية!**\n"
            f"👤 **الاسم:** {data.get('name')}\n"
            f"🏛️ **التاون هول:** TH{data.get('townHallLevel')}\n\n"
            f"💵 أدخل السعر المطلوب (مثال: $50 أو 200 ريال):",
            parse_mode="Markdown"
        )
    else:
        await msg.answer("❌ لم يتم العثور على القرية في خوادم اللعبة. تأكد من الـ Tag وأرسله مجدداً:")

@dp.message(SellAccountState.waiting_for_price)
async def sell_price(msg: types.Message, state: FSMContext):
    price = msg.text.strip()
    user_data = await state.get_data()
    
    async with aiosqlite.connect('clash_bot.db') as db:
        await db.execute(
            'INSERT INTO accounts (seller_id, seller_username, tag, name, th_level, trophies, price) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (msg.from_user.id, msg.from_user.username or "بدون يوزر", user_data['tag'], user_data['name'], user_data['th'], user_data['trophies'], price)
        )
        await db.commit()

    await msg.answer("🎉 تم إضافة الحساب بنجاح إلى سوق الحسابات والعرض متاح للجميع الآن!", reply_markup=main_reply_keyboard())
    await state.clear()

@dp.message(F.text == "🛒 سوق الحسابات")
async def market_list(msg: types.Message):
    async with aiosqlite.connect('clash_bot.db') as db:
        async with db.execute('SELECT id, name, th_level, trophies, price, tag FROM accounts WHERE status = "AVAILABLE" ORDER BY id DESC LIMIT 10') as cursor:
            rows = await cursor.fetchall()

    if not rows:
        await msg.answer("🛒 السوق فارغ حالياً. يمكنك إضافة حسابك للبيع عبر زر '➕ عرض حساب للبيع'.")
        return

    await msg.answer("🛒 **الحسابات المعروضة للبيع حالياً:**", parse_mode="Markdown")
    for row in rows:
        acc_id, name, th, trophies, price, tag = row
        card = (
            f"🆔 **رقم العرض:** #{acc_id}\n"
            f"🏰 **اسم القرية:** {name}\n"
            f"🏛️ **التاون هول:** TH{th}\n"
            f"🏆 **الكؤوس:** {trophies}\n"
            f"💵 **السعر:** {price}\n"
            f"🏷️ **الـ Tag:** `{tag}`"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔒 طلب شراء عبر الوساطة", callback_data=f"buy_{acc_id}")]
        ])
        await msg.answer(card, parse_mode="Markdown", reply_markup=kb)

@dp.callback_query(F.data.startswith("buy_"))
async def buy_request(call: CallbackQuery):
    acc_id = call.data.split("_")[1]
    await call.message.answer(f"✅ تم فتح طلب شراء للحساب #{acc_id}.\nتواصل مع الدعم في قسم 'حسابي والدعم' للبدء في نقل ملكية الحساب وإتمام الضمان.")
    await call.answer()

@dp.message(F.text == "👤 حسابي والدعم")
async def profile_info(msg: types.Message):
    text = (
        f"👤 **بيانات حسابك:**\n"
        f"• المعرف (ID): `{msg.from_user.id}`\n"
        f"• الاسم: {msg.from_user.first_name}\n\n"
        f"📞 **الدعم الفني والإدارة:**\nلأي استفسار أو لفتح غرفة وساطة ومراجعة صفقاتك."
    )
    await msg.answer(text, parse_mode="Markdown")

# --- خادم الويب السريع لمنع خطأ Timed Out في Render ---
async def handle_ping(request):
    return web.Response(text="Bot is live!")

async def start_services():
    app = web.Application()
    app.router.add_get('/', handle_ping)
    
    port = int(os.environ.get("PORT", 10000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    await init_db()
    print("🚀 البوت والسيرفر المجاني يعملان بنجاح...")
    
    # تشغيل استعلامات التليجرام بداخل نفس الـ Loop
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(start_services())
