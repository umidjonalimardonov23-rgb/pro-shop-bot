"""
╔══════════════════════════════════════════════════════════╗
║          🛍️  PRO SHOP BOT  —  Kengaytirilgan v2.0        ║
╠══════════════════════════════════════════════════════════╣
║  ✅ Mahsulot qo'shish: FAQAT O'ZBEK tilida yoziladi      ║
║  ✅ Kanalga avtomatik post                               ║
║  ✅ 3 til: O'zbek / Rus / Ingliz                         ║
║  ✅ To'lov: Click, Payme, Karta                          ║
║  ✅ Buyurtma holati + admin izoh                         ║
║  ✅ Admin panel (to'liq boshqaruv)                       ║
║  ✅ Mijoz: buyurtmalar tarixi                             ║
║  ✅ SQLite baza                                           ║
║  ✅ Mahsulot qidirish, reyting, sharhlar                  ║
║  ✅ Promo-kod va chegirmalar                              ║
║  ✅ Referal tizim                                         ║
╚══════════════════════════════════════════════════════════╝
"""

import logging
import sqlite3
import os
import csv
import io
from datetime import datetime, timedelta
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ConversationHandler, ContextTypes, filters
)

# ═══════════════════════════════════════════════════════════
#  ⚙️  SOZLAMALAR
# ═══════════════════════════════════════════════════════════
BOT_TOKEN  = os.environ.get("BOT_TOKEN", "")
ADMIN_ID   = int(os.environ.get("ADMIN_ID", "8787603995"))
CHANNEL_ID = os.environ.get("CHANNEL_ID", "@Shop_market_uzz")

CARD_NUMBER = os.environ.get("CARD_NUMBER", "9860 6067 6080 6673")
CARD_OWNER  = os.environ.get("CARD_OWNER",  "Alimardonov Umidjon")
CARD_PHONE  = os.environ.get("CARD_PHONE",  "+998953909477")

REFERRAL_BONUS      = 5_000   # so'm
LOW_STOCK_THRESHOLD = 5
DB_PATH             = "shop.db"

logging.basicConfig(
    format="%(asctime)s — %(levelname)s — %(message)s",
    level=logging.INFO
)

# ═══════════════════════════════════════════════════════════
#  🌐  TILLAR
# ═══════════════════════════════════════════════════════════
TEXTS = {
    "uz": {
        "welcome":       "👋 Salom, *{name}*! Xush kelibsiz 🎉\n\n🌐 Tilni tanlang:",
        "welcome_back":  "👋 Xush kelibsiz, *{name}*! 🎉\n\n👇 Pastdagi menyudan tanlang:",
        "choose_lang":   "🌐 Tilni tanlang:",
        "catalog":       "🗂 Kategoriyani tanlang:",
        "no_products":   "😔 Bu kategoriyada mahsulot yo'q.",
        "order_name":    "👤 Ismingizni kiriting:",
        "order_phone":   "📱 Telefon raqamingizni yuboring:",
        "order_address": "🏠 Manzilingizni kiriting:",
        "order_qty":     "🔢 Nechta olmoqchisiz?",
        "order_promo":   "🎁 Promo-kod bormi?\n(/skip — o'tkazib yuborish):",
        "promo_applied": "✅ Promo-kod qo'llandi! Chegirma: *{discount}*",
        "promo_invalid": "❌ Noto'g'ri promo-kod.\n/skip yozing yoki to'g'ri kodni kiriting:",
        "order_zone":    "🚚 Yetkazib berish hududini tanlang:",
        "order_pay":     "💳 To'lov usulini tanlang:",
        "order_done":    (
            "✅ *Buyurtma qabul qilindi!*\n\n"
            "📦 {name}\n"
            "💰 {price} × {qty} = {subtotal} so'm\n"
            "🎁 Chegirma: -{discount} so'm\n"
            "🚚 Yetkazish: {delivery} so'm\n"
            "💳 *Jami: {total} so'm*\n\n"
            "⏳ Admin tez orada bog'lanadi!"
        ),
        "my_orders":     "📋 *Sizning buyurtmalaringiz:*",
        "no_orders":     "😔 Hali buyurtma yo'q.",
        "pay_card":      "💳 Karta orqali to'lash",
        "pay_click":     "⚡ Click orqali to'lash",
        "pay_payme":     "💚 Payme orqali to'lash",
        "card_info":     (
            "💳 *Karta raqami:*\n`{card}`\n"
            "👤 *Egasi:* {owner}\n"
            "📞 *Ulangan raqam:* {phone}\n"
            "💰 *Summa:* {total} so'm\n\n"
            "✅ To'lovni amalga oshirib, chekni yuboring."
        ),
        "send_receipt":  "🧾 Chekni yuboring (surat yoki screenshot):",
        "receipt_sent":  "✅ Chek qabul qilindi! Admin tekshiradi.",
        "cancel":        "❌ Bekor qilindi.",
        "back":          "⬅️ Orqaga",
        "buy":           "🛒 Buyurtma berish",
        "status_new":       "🆕 Yangi",
        "status_confirmed": "✅ Tasdiqlandi",
        "status_delivered": "🚚 Yetkazildi",
        "status_cancelled": "❌ Bekor qilindi",
        "search_ask":    "🔍 Qidiruv so'zini kiriting:",
        "search_no":     "😔 Hech narsa topilmadi.",
        "search_found":  "🔍 *Topildi ({count} ta):*",
        "rate_ask":      "⭐ Buyurtmangizni baholang (1-5):",
        "rate_comment":  "💬 Izoh qoldiring\n(/skip — o'tkazib yuborish):",
        "rate_thanks":   "🙏 Fikringiz uchun rahmat!",
        "referral_info": (
            "👥 *Referal dasturi*\n\n"
            "🔗 Sizning havolangiz:\n{link}\n\n"
            "🎁 Har bir do'stingiz uchun *{bonus} so'm* bonus!\n\n"
            "👤 Taklif qilganlar: *{count}* kishi\n"
            "💰 Jami bonus: *{total} so'm*"
        ),
        "balance_info":  "💰 Sizning balans: *{balance} so'm*",
        "balance_used":  "✅ Balansdan *{amount} so'm* ishlatildi.",
    },
    "ru": {
        "welcome":       "👋 Привет, *{name}*!\n\n🌐 Выберите язык:",
        "welcome_back":  "🏠 С возвращением, *{name}*! 🎉\n\n👇 Выберите из меню:",
        "choose_lang":   "🌐 Выберите язык:",
        "catalog":       "🗂 Выберите категорию:",
        "no_products":   "😔 В этой категории нет товаров.",
        "order_name":    "👤 Введите ваше имя:",
        "order_phone":   "📱 Отправьте ваш номер телефона:",
        "order_address": "🏠 Введите ваш адрес:",
        "order_qty":     "🔢 Сколько штук хотите?",
        "order_promo":   "🎁 Есть промокод?\n(/skip — пропустить):",
        "promo_applied": "✅ Промокод применён! Скидка: *{discount}*",
        "promo_invalid": "❌ Неверный промокод.\nНапишите /skip или введите правильный код:",
        "order_zone":    "🚚 Выберите зону доставки:",
        "order_pay":     "💳 Выберите способ оплаты:",
        "order_done":    (
            "✅ *Заказ принят!*\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📦 {name}\n"
            "💰 {price} × {qty} = {subtotal} сум\n"
            "🎁 Скидка: -{discount} сум\n"
            "🚚 Доставка: {delivery} сум\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "💳 *Итого: {total} сум*\n\n"
            "⏳ Администратор скоро свяжется!"
        ),
        "my_orders":     "📋 *Ваши заказы:*",
        "no_orders":     "😔 Заказов пока нет.",
        "pay_card":      "💳 Оплата картой",
        "pay_click":     "⚡ Оплата Click",
        "pay_payme":     "💚 Оплата Payme",
        "card_info":     (
            "💳 *Номер карты:*\n`{card}`\n"
            "👤 *Владелец:* {owner}\n"
            "📞 *Номер телефона:* {phone}\n"
            "💰 *Сумма:* {total} сум\n\n"
            "✅ Переведите и отправьте чек."
        ),
        "send_receipt":  "🧾 Отправьте чек (фото или скриншот):",
        "receipt_sent":  "✅ Чек получен! Администратор проверит.",
        "cancel":        "❌ Отменено.",
        "back":          "⬅️ Назад",
        "buy":           "🛒 Заказать",
        "status_new":       "🆕 Новый",
        "status_confirmed": "✅ Подтверждён",
        "status_delivered": "🚚 Доставлен",
        "status_cancelled": "❌ Отменён",
        "search_ask":    "🔍 Введите поисковый запрос:",
        "search_no":     "😔 Ничего не найдено.",
        "search_found":  "🔍 *Найдено ({count} шт.):*",
        "rate_ask":      "⭐ Оцените ваш заказ (1-5):",
        "rate_comment":  "💬 Оставьте комментарий\n(/skip — пропустить):",
        "rate_thanks":   "🙏 Спасибо за отзыв!",
        "referral_info": (
            "👥 *Реферальная программа*\n\n"
            "🔗 Ваша ссылка:\n{link}\n\n"
            "🎁 За каждого друга *{bonus} сум* бонус!\n\n"
            "👤 Приглашено: *{count}* чел.\n"
            "💰 Всего бонусов: *{total} сум*"
        ),
        "balance_info":  "💰 Ваш баланс: *{balance} сум*",
        "balance_used":  "✅ С баланса списано *{amount} сум*.",
    },
    "en": {
        "welcome":       "👋 Hello, *{name}*!\n\n🌐 Choose language:",
        "welcome_back":  "🏠 Welcome back, *{name}*! 🎉\n\n👇 Choose from the menu:",
        "choose_lang":   "🌐 Choose language:",
        "catalog":       "🗂 Choose a category:",
        "no_products":   "😔 No products in this category.",
        "order_name":    "👤 Enter your name:",
        "order_phone":   "📱 Send your phone number:",
        "order_address": "🏠 Enter your address:",
        "order_qty":     "🔢 How many do you want?",
        "order_promo":   "🎁 Have a promo code?\n(/skip — skip):",
        "promo_applied": "✅ Promo code applied! Discount: *{discount}*",
        "promo_invalid": "❌ Invalid promo code.\nType /skip or enter the correct code:",
        "order_zone":    "🚚 Choose delivery zone:",
        "order_pay":     "💳 Choose payment method:",
        "order_done":    (
            "✅ *Order accepted!*\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📦 {name}\n"
            "💰 {price} × {qty} = {subtotal} UZS\n"
            "🎁 Discount: -{discount} UZS\n"
            "🚚 Delivery: {delivery} UZS\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "💳 *Total: {total} UZS*\n\n"
            "⏳ Admin will contact you soon!"
        ),
        "my_orders":     "📋 *Your orders:*",
        "no_orders":     "😔 No orders yet.",
        "pay_card":      "💳 Pay by card",
        "pay_click":     "⚡ Pay via Click",
        "pay_payme":     "💚 Pay via Payme",
        "card_info":     (
            "💳 *Card number:*\n`{card}`\n"
            "👤 *Owner:* {owner}\n"
            "📞 *Phone:* {phone}\n"
            "💰 *Amount:* {total} UZS\n\n"
            "✅ Transfer and send the receipt."
        ),
        "send_receipt":  "🧾 Send receipt (photo or screenshot):",
        "receipt_sent":  "✅ Receipt received! Admin will verify.",
        "cancel":        "❌ Cancelled.",
        "back":          "⬅️ Back",
        "buy":           "🛒 Order",
        "status_new":       "🆕 New",
        "status_confirmed": "✅ Confirmed",
        "status_delivered": "🚚 Delivered",
        "status_cancelled": "❌ Cancelled",
        "search_ask":    "🔍 Enter search query:",
        "search_no":     "😔 Nothing found.",
        "search_found":  "🔍 *Found ({count} items):*",
        "rate_ask":      "⭐ Rate your order (1-5):",
        "rate_comment":  "💬 Leave a comment\n(/skip — skip):",
        "rate_thanks":   "🙏 Thank you for your review!",
        "referral_info": (
            "👥 *Referral Program*\n\n"
            "🔗 Your link:\n{link}\n\n"
            "🎁 Earn *{bonus} UZS* for each friend!\n\n"
            "👤 Referred: *{count}* people\n"
            "💰 Total bonus: *{total} UZS*"
        ),
        "balance_info":  "💰 Your balance: *{balance} UZS*",
        "balance_used":  "✅ *{amount} UZS* deducted from balance.",
    }
}

CATEGORIES = {
    "uz": ["👗 Kiyim", "👟 Poyabzal", "💍 Aksessuarlar", "🎒 Sumkalar", "🧴 Kosmetika"],
    "ru": ["👗 Одежда", "👟 Обувь", "💍 Аксессуары", "🎒 Сумки", "🧴 Косметика"],
    "en": ["👗 Clothing", "👟 Footwear", "💍 Accessories", "🎒 Bags", "🧴 Cosmetics"],
}
CAT_KEYS = ["clothing", "footwear", "accessories", "bags", "cosmetics"]

DEFAULT_ZONES = [
    ("Toshkent shahri",   "Город Ташкент",          "Tashkent city",    10_000),
    ("Toshkent viloyati", "Ташкентская область",    "Tashkent region",  20_000),
    ("Samarqand",         "Самарканд",               "Samarkand",        30_000),
    ("Buxoro",            "Бухара",                  "Bukhara",          30_000),
    ("Farg'ona",          "Фергана",                 "Fergana",          25_000),
    ("Andijon",           "Андижан",                 "Andijan",          25_000),
    ("Namangan",          "Наманган",                "Namangan",         25_000),
    ("Boshqa viloyat",    "Другой регион",           "Other region",     40_000),
]

def t(lang, key, **kw):
    text = TEXTS.get(lang, TEXTS["uz"]).get(key, key)
    return text.format(**kw) if kw else text

# ═══════════════════════════════════════════════════════════
#  🗄️  DATABASE
# ═══════════════════════════════════════════════════════════
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS products (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        category    TEXT,
        photo_id    TEXT,
        name_uz     TEXT,
        name_ru     TEXT,
        name_en     TEXT,
        price       INTEGER,
        desc_uz     TEXT,
        desc_ru     TEXT,
        desc_en     TEXT,
        stock       INTEGER DEFAULT 999,
        active      INTEGER DEFAULT 1,
        views       INTEGER DEFAULT 0,
        sold_count  INTEGER DEFAULT 0,
        created_at  TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS orders (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id       INTEGER,
        username      TEXT,
        lang          TEXT,
        product_id    INTEGER,
        product_name  TEXT,
        qty           INTEGER,
        price         INTEGER,
        total         INTEGER,
        buyer_name    TEXT,
        phone         TEXT,
        address       TEXT,
        payment       TEXT,
        status        TEXT DEFAULT 'new',
        receipt_file_id TEXT,
        discount      INTEGER DEFAULT 0,
        delivery_price INTEGER DEFAULT 0,
        delivery_zone  TEXT DEFAULT '',
        promo_code     TEXT DEFAULT '',
        created_at    TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id       INTEGER PRIMARY KEY,
        lang          TEXT DEFAULT 'uz',
        username      TEXT,
        full_name     TEXT,
        balance       INTEGER DEFAULT 0,
        referral_count INTEGER DEFAULT 0,
        referred_by   INTEGER DEFAULT 0,
        created_at    TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS promo_codes (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        code           TEXT UNIQUE,
        discount_type  TEXT DEFAULT 'percent',
        discount_value INTEGER DEFAULT 10,
        max_uses       INTEGER DEFAULT 100,
        uses_count     INTEGER DEFAULT 0,
        active         INTEGER DEFAULT 1,
        created_at     TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS reviews (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id   INTEGER,
        user_id    INTEGER,
        product_id INTEGER,
        rating     INTEGER,
        comment    TEXT,
        created_at TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS delivery_zones (
        id      INTEGER PRIMARY KEY AUTOINCREMENT,
        name_uz TEXT, name_ru TEXT, name_en TEXT,
        price   INTEGER,
        active  INTEGER DEFAULT 1
    )""")
    existing = conn.execute("SELECT COUNT(*) FROM delivery_zones").fetchone()[0]
    if existing == 0:
        for z in DEFAULT_ZONES:
            conn.execute(
                "INSERT INTO delivery_zones(name_uz,name_ru,name_en,price) VALUES(?,?,?,?)", z
            )
    conn.commit()
    conn.close()

def db():
    return sqlite3.connect(DB_PATH)

def get_lang(uid):
    with db() as c:
        r = c.execute("SELECT lang FROM users WHERE user_id=?", (uid,)).fetchone()
    return r[0] if r else "uz"

def set_lang(uid, lang, username="", full_name=""):
    with db() as c:
        c.execute(
            """INSERT INTO users(user_id,lang,username,full_name,created_at)
               VALUES(?,?,?,?,?)
               ON CONFLICT(user_id) DO UPDATE SET lang=excluded.lang""",
            (uid, lang, username, full_name, datetime.now().isoformat())
        )

def get_user(uid):
    with db() as c:
        return c.execute("SELECT * FROM users WHERE user_id=?", (uid,)).fetchone()

def add_balance(uid, amt):
    with db() as c:
        c.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (amt, uid))

def use_balance(uid, amt):
    with db() as c:
        c.execute("UPDATE users SET balance=MAX(0,balance-?) WHERE user_id=?", (amt, uid))

def process_referral(new_uid, referrer_id):
    with db() as c:
        row = c.execute("SELECT referred_by FROM users WHERE user_id=?", (new_uid,)).fetchone()
        if row and row[0] == 0 and referrer_id != new_uid:
            c.execute("UPDATE users SET referred_by=? WHERE user_id=?", (referrer_id, new_uid))
            c.execute(
                "UPDATE users SET balance=balance+?, referral_count=referral_count+1 WHERE user_id=?",
                (REFERRAL_BONUS, referrer_id)
            )

def get_products(category=None):
    with db() as c:
        if category:
            return c.execute(
                "SELECT * FROM products WHERE category=? AND active=1 ORDER BY id DESC", (category,)
            ).fetchall()
        return c.execute("SELECT * FROM products WHERE active=1 ORDER BY id DESC").fetchall()

def search_products(query):
    q = f"%{query}%"
    with db() as c:
        return c.execute(
            """SELECT * FROM products WHERE active=1 AND (
                name_uz LIKE ? OR name_ru LIKE ? OR name_en LIKE ?
                OR desc_uz LIKE ? OR desc_ru LIKE ? OR desc_en LIKE ?
            ) ORDER BY id DESC LIMIT 20""",
            (q, q, q, q, q, q)
        ).fetchall()

def add_product(category, photo_id, name, price, desc, stock=999):
    """Faqat bitta tilda nom va tavsif — qolganlariga avtomatik nusxalanadi."""
    with db() as c:
        cur = c.execute(
            """INSERT INTO products
               (category,photo_id,name_uz,name_ru,name_en,price,desc_uz,desc_ru,desc_en,stock,created_at)
               VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
            (category, photo_id,
             name, name, name,
             price,
             desc, desc, desc,
             stock,
             datetime.now().isoformat())
        )
        return cur.lastrowid

def delete_product(pid):
    with db() as c:
        c.execute("UPDATE products SET active=0 WHERE id=?", (pid,))

def decrease_stock(pid, qty):
    with db() as c:
        c.execute("UPDATE products SET stock=MAX(0,stock-?) WHERE id=?", (qty, pid))
        new_stock = c.execute("SELECT stock FROM products WHERE id=?", (pid,)).fetchone()[0]
        if new_stock == 0:
            c.execute("UPDATE products SET active=0 WHERE id=?", (pid,))
    return new_stock

def set_stock(pid, qty):
    with db() as c:
        c.execute(
            "UPDATE products SET stock=?, active=? WHERE id=?",
            (qty, 1 if qty > 0 else 0, pid)
        )

def get_low_stock():
    with db() as c:
        return c.execute(
            "SELECT id,name_uz,stock FROM products WHERE active=1 AND stock<=? ORDER BY stock",
            (LOW_STOCK_THRESHOLD,)
        ).fetchall()

def add_order(uid, username, lang, product_id, product_name, qty, price,
              buyer_name, phone, address, payment,
              discount=0, delivery_price=0, delivery_zone="", promo_code=""):
    subtotal = qty * price
    total    = max(0, subtotal - discount) + delivery_price
    with db() as c:
        cur = c.execute(
            """INSERT INTO orders
               (user_id,username,lang,product_id,product_name,qty,price,total,
                buyer_name,phone,address,payment,status,
                discount,delivery_price,delivery_zone,promo_code,created_at)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,?,'new',?,?,?,?,?)""",
            (uid, username, lang, product_id, product_name, qty, price, total,
             buyer_name, phone, address, payment,
             discount, delivery_price, delivery_zone, promo_code,
             datetime.now().isoformat())
        )
        return cur.lastrowid

def get_orders(uid=None):
    with db() as c:
        if uid:
            return c.execute(
                "SELECT * FROM orders WHERE user_id=? ORDER BY id DESC LIMIT 10", (uid,)
            ).fetchall()
        return c.execute("SELECT * FROM orders ORDER BY id DESC LIMIT 50").fetchall()

def update_order_status(oid, status):
    with db() as c:
        c.execute("UPDATE orders SET status=? WHERE id=?", (status, oid))

def update_receipt(oid, file_id):
    with db() as c:
        c.execute("UPDATE orders SET receipt_file_id=? WHERE id=?", (file_id, oid))

def update_product_field(pid, field, value):
    allowed = {"name_uz", "price", "desc_uz", "stock"}
    if field not in allowed:
        return
    with db() as c:
        c.execute(f"UPDATE products SET {field}=? WHERE id=?", (value, pid))

def get_stats():
    with db() as c:
        tot_o  = c.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        tot_r  = c.execute("SELECT COALESCE(SUM(total),0) FROM orders WHERE status!='cancelled'").fetchone()[0]
        new_o  = c.execute("SELECT COUNT(*) FROM orders WHERE status='new'").fetchone()[0]
        tot_u  = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        tot_p  = c.execute("SELECT COUNT(*) FROM products WHERE active=1").fetchone()[0]
        avg_r  = c.execute("SELECT COALESCE(AVG(rating),0) FROM reviews").fetchone()[0]
    return tot_o, tot_r, new_o, tot_u, tot_p, avg_r

def increment_views(pid):
    with db() as c:
        c.execute("UPDATE products SET views=views+1 WHERE id=?", (pid,))

def increment_sold(pid, qty):
    with db() as c:
        c.execute("UPDATE products SET sold_count=sold_count+? WHERE id=?", (qty, pid))

def get_top_products(limit=10):
    with db() as c:
        return c.execute(
            "SELECT id,name_uz,sold_count,views,price FROM products ORDER BY sold_count DESC LIMIT ?",
            (limit,)
        ).fetchall()

def get_stuck_orders(hours=2):
    threshold = (datetime.now() - timedelta(hours=hours)).isoformat()
    with db() as c:
        return c.execute(
            "SELECT id,product_name,buyer_name,phone,created_at FROM orders "
            "WHERE status='new' AND created_at<? ORDER BY id",
            (threshold,)
        ).fetchall()

def get_today_stats():
    today = datetime.now().strftime("%Y-%m-%d")
    with db() as c:
        o = c.execute("SELECT COUNT(*) FROM orders WHERE created_at LIKE ?", (f"{today}%",)).fetchone()[0]
        r = c.execute("SELECT COALESCE(SUM(total),0) FROM orders WHERE created_at LIKE ? AND status!='cancelled'", (f"{today}%",)).fetchone()[0]
        u = c.execute("SELECT COUNT(*) FROM users WHERE created_at LIKE ?", (f"{today}%",)).fetchone()[0]
    return o, r, u

def check_promo(code):
    with db() as c:
        return c.execute(
            "SELECT * FROM promo_codes WHERE code=? AND active=1 AND uses_count<max_uses",
            (code.upper(),)
        ).fetchone()

def use_promo(code):
    with db() as c:
        c.execute("UPDATE promo_codes SET uses_count=uses_count+1 WHERE code=?", (code.upper(),))

def add_promo_code(code, dtype, dval, max_uses):
    with db() as c:
        try:
            c.execute(
                "INSERT INTO promo_codes(code,discount_type,discount_value,max_uses,created_at) VALUES(?,?,?,?,?)",
                (code.upper(), dtype, dval, max_uses, datetime.now().isoformat())
            )
            return True
        except Exception:
            return False

def get_promo_codes():
    with db() as c:
        return c.execute("SELECT * FROM promo_codes ORDER BY id DESC").fetchall()

def add_review(oid, uid, pid, rating, comment):
    with db() as c:
        c.execute(
            "INSERT INTO reviews(order_id,user_id,product_id,rating,comment,created_at) VALUES(?,?,?,?,?,?)",
            (oid, uid, pid, rating, comment, datetime.now().isoformat())
        )

def get_product_reviews(pid):
    with db() as c:
        return c.execute(
            "SELECT rating,comment FROM reviews WHERE product_id=? ORDER BY id DESC LIMIT 5",
            (pid,)
        ).fetchall()

def get_avg_rating(pid):
    with db() as c:
        r = c.execute("SELECT AVG(rating),COUNT(*) FROM reviews WHERE product_id=?", (pid,)).fetchone()
    return r[0] or 0, r[1] or 0

def get_zones(lang):
    col = {"uz": 1, "ru": 2, "en": 3}[lang]
    with db() as c:
        zones = c.execute("SELECT id,name_uz,name_ru,name_en,price FROM delivery_zones WHERE active=1").fetchall()
    return [(z[0], z[col], z[4]) for z in zones]

def get_zone_price(zid):
    with db() as c:
        r = c.execute("SELECT price FROM delivery_zones WHERE id=?", (zid,)).fetchone()
    return r[0] if r else 0

def get_zone_name(zid, lang):
    col = {"uz": 1, "ru": 2, "en": 3}[lang]
    with db() as c:
        r = c.execute("SELECT name_uz,name_ru,name_en FROM delivery_zones WHERE id=?", (zid,)).fetchone()
    return r[col - 1] if r else ""

# ═══════════════════════════════════════════════════════════
#  🔢  CONVERSATION STATES
# ═══════════════════════════════════════════════════════════
# Mahsulot qo'shish (admin)
AP_CAT, AP_PHOTO, AP_NAME, AP_PRICE, AP_DESC, AP_STOCK = range(6)

# Buyurtma
O_NAME, O_PHONE, O_ADDRESS, O_QTY, O_PROMO, O_ZONE, O_PAY, O_RECEIPT = range(20, 28)

# Qidirish
S_QUERY = 30

# Sharh
R_COMMENT = 40

# Admin amallar
ADM_PROMO_CODE, ADM_PROMO_TYPE, ADM_PROMO_VAL, ADM_PROMO_MAX = range(50, 54)
ADM_BROADCAST = 60
ADM_ZONE_NAME_UZ, ADM_ZONE_NAME_RU, ADM_ZONE_NAME_EN, ADM_ZONE_PRICE = range(62, 66)
ADM_STOCK_QTY = 67
ADM_NOTE      = 70

# Mahsulot tahrirlash (admin)
EP_SELECT, EP_FIELD, EP_VALUE = range(75, 78)

# Savat (korzinka) checkout
CART_NAME, CART_PHONE, CART_ADDR = range(80, 83)

# Chek kutish: {user_id: order_id}  — ConversationHandler tashqarisida ishlatiladi
PENDING_RECEIPT: dict = {}

# ═══════════════════════════════════════════════════════════
#  🌐  TIL TANLASH
# ═══════════════════════════════════════════════════════════
def lang_kb():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🇺🇿 O'zbek",   callback_data="lang_uz"),
        InlineKeyboardButton("🇷🇺 Русский",  callback_data="lang_ru"),
        InlineKeyboardButton("🇬🇧 English",  callback_data="lang_en"),
    ]])

# ── Menyu tugma matnlari (barcha tillar) ─────────────────
MENU_LABELS = {
    "uz": {
        "catalog":  "🛍 Katalog",
        "search":   "🔍 Qidirish",
        "orders":   "📦 Buyurtmalarim",
        "cart":     "🛒 Savat",
        "balance":  "💰 Balansim",
        "referral": "👥 Referal",
        "lang":     "🌐 Til",
        "admin":    "🛠 Admin Panel",
    },
    "ru": {
        "catalog":  "🛍 Каталог",
        "search":   "🔍 Поиск",
        "orders":   "📦 Мои заказы",
        "cart":     "🛒 Корзина",
        "balance":  "💰 Баланс",
        "referral": "👥 Реферал",
        "lang":     "🌐 Язык",
        "admin":    "🛠 Admin Panel",
    },
    "en": {
        "catalog":  "🛍 Catalog",
        "search":   "🔍 Search",
        "orders":   "📦 My Orders",
        "cart":     "🛒 Cart",
        "balance":  "💰 Balance",
        "referral": "👥 Referral",
        "lang":     "🌐 Language",
        "admin":    "🛠 Admin Panel",
    },
}

# Barcha tillar uchun matn → action mapping (text handler uchun)
ALL_MENU_TEXTS: dict = {}
for _lng, _lbls in MENU_LABELS.items():
    for _act, _lbl in _lbls.items():
        ALL_MENU_TEXTS[_lbl] = _act

def main_menu_kb(uid, lang):
    """Pastki ReplyKeyboard — to'rtburchak tugmalar."""
    L = MENU_LABELS.get(lang, MENU_LABELS["uz"])
    rows = [
        [L["catalog"],  L["search"]  ],
        [L["orders"],   L["cart"]    ],
        [L["balance"],  L["referral"]],
        [L["lang"]],
    ]
    if uid == ADMIN_ID:
        rows[-1].append(L["admin"])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, is_persistent=True)

async def show_main_menu(update, ctx, lang, via_query=False):
    user = update.effective_user
    kb   = main_menu_kb(user.id, lang)
    text = t(lang, "welcome_back", name=user.first_name)
    if via_query and update.callback_query:
        # Inline xabarni o'chirmaymiz, shunchaki yangi xabar
        try:
            await update.callback_query.message.reply_text(text, reply_markup=kb, parse_mode="Markdown")
        except Exception:
            pass
    else:
        await update.message.reply_text(text, reply_markup=kb, parse_mode="Markdown")

async def menu_text_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Pastki klaviatura tugmalarini ushlaydi."""
    txt  = update.message.text.strip()
    act  = ALL_MENU_TEXTS.get(txt)
    uid  = update.effective_user.id
    lang = get_lang(uid)
    if act == "catalog":
        await catalog(update, ctx)
    elif act == "search":
        await search_start(update, ctx)
    elif act == "orders":
        await my_orders(update, ctx)
    elif act == "cart":
        await cart_view_cmd(update, ctx)
    elif act == "balance":
        await balance_cmd(update, ctx)
    elif act == "referral":
        await referral(update, ctx)
    elif act == "lang":
        await update.message.reply_text(t(lang, "choose_lang"), reply_markup=lang_kb())
    elif act == "admin":
        if uid == ADMIN_ID:
            await admin_menu(update, ctx)
        else:
            await update.message.reply_text("❌ Ruxsat yo'q.")

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user     = update.effective_user
    args     = ctx.args
    existing = get_user(user.id)

    if args and args[0].startswith("ref_"):
        try:
            referrer_id = int(args[0].split("_")[1])
            if existing:
                process_referral(user.id, referrer_id)
        except Exception:
            pass

    if args and args[0].startswith("product_"):
        try:
            pid = int(args[0].split("_")[1])
        except Exception:
            pid = None
        if pid:
            ctx.user_data["deeplink_pid"] = pid
            lang = get_lang(user.id)
            await show_product(update, ctx, pid, lang)
            return

    if existing:
        lang = get_lang(user.id)
        await show_main_menu(update, ctx, lang)
        return

    set_lang(user.id, "uz", user.username or "", user.full_name or "")
    await update.message.reply_text(
        t("uz", "welcome", name=user.first_name),
        reply_markup=lang_kb()
    )

async def set_language(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.split("_")[1]
    user = query.from_user
    set_lang(user.id, lang, user.username or "", user.full_name or "")
    pid = ctx.user_data.pop("deeplink_pid", None)
    if pid:
        await show_product(update, ctx, pid, lang, via_query=True)
        return
    await show_main_menu(update, ctx, lang, via_query=True)

# ═══════════════════════════════════════════════════════════
#  🗂  KATALOG
# ═══════════════════════════════════════════════════════════
async def catalog(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update.effective_user.id)
    cats = CATEGORIES[lang]
    buttons = [
        [InlineKeyboardButton(name, callback_data=f"cat_{key}")]
        for name, key in zip(cats, CAT_KEYS)
    ]
    buttons.append([InlineKeyboardButton("🏠 Bosh menyu", callback_data="menu_home")])
    kb = InlineKeyboardMarkup(buttons)
    if update.message:
        await update.message.reply_text(t(lang, "catalog"), reply_markup=kb)
    else:
        try:
            await update.callback_query.edit_message_text(t(lang, "catalog"), reply_markup=kb)
        except Exception:
            await update.callback_query.message.reply_text(t(lang, "catalog"), reply_markup=kb)

async def show_category(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang    = get_lang(query.from_user.id)
    cat_key = query.data.split("_", 1)[1]
    products = get_products(cat_key)

    if not products:
        await query.edit_message_text(
            t(lang, "no_products"),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(t(lang, "back"), callback_data="back_catalog")
            ]])
        )
        return

    name_col = {"uz": 3, "ru": 4, "en": 5}[lang]
    buttons = []
    for p in products:
        avg, cnt = get_avg_rating(p[0])
        stars = f" ⭐{avg:.1f}({cnt})" if cnt > 0 else ""
        label = f"{p[name_col]} — {p[6]:,} so'm{stars}"
        buttons.append([InlineKeyboardButton(label, callback_data=f"prod_{p[0]}")])
    buttons.append([InlineKeyboardButton(t(lang, "back"), callback_data="back_catalog")])
    await query.edit_message_text(
        f"📦 *{len(products)} ta mahsulot:*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def show_product_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    pid  = int(query.data.split("_")[1])
    lang = get_lang(query.from_user.id)
    increment_views(pid)
    await show_product(update, ctx, pid, lang, via_query=True)

async def show_product(update, ctx, pid, lang, via_query=False):
    with db() as c:
        p = c.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
    if not p:
        msg = "❌ Mahsulot topilmadi."
        if via_query:
            await update.callback_query.message.reply_text(msg)
        else:
            await update.message.reply_text(msg)
        return

    name_col = {"uz": 3, "ru": 4, "en": 5}[lang]
    desc_col = {"uz": 7, "ru": 8, "en": 9}[lang]
    avg, cnt = get_avg_rating(pid)
    stars_str = f"\n⭐ *Reyting:* {avg:.1f}/5 ({cnt} ta sharh)" if cnt > 0 else ""

    stock = p[10]
    if stock == 0:
        stock_str = "❌ *Tugagan*"
    elif stock <= LOW_STOCK_THRESHOLD:
        stock_str = f"⚠️ *Qoldiq: {stock} dona* (kam qoldi!)"
    else:
        stock_str = f"✅ *Mavjud:* {stock} dona"

    views_str = f"👁 {p[12]:,} ko'rishlar  •  🛒 {p[13]:,} ta sotilgan" if len(p) > 13 else ""

    reviews = get_product_reviews(pid)
    rev_str = ""
    if reviews:
        rev_str = "\n\n💬 *Sharhlar:*\n"
        for r in reviews[:3]:
            rev_str += f"{'⭐'*r[0]}" + (f" — _{r[1]}_" if r[1] else "") + "\n"

    caption = (
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 *{p[name_col]}*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 *Narxi: {p[6]:,} so'm*\n"
        f"{stock_str}"
        f"{stars_str}\n"
        f"{views_str}\n\n"
        f"📝 {p[desc_col]}"
        f"{rev_str}"
    )

    cart = ctx.user_data.get("cart", {})
    cart_count = sum(v["qty"] for v in cart.values())
    cart_label = f"🛒 Savat ({cart_count} ta)" if cart_count > 0 else "🛒 Savat"

    if stock > 0:
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"⚡ Hoziroq buyurtma", callback_data=f"order_{pid}"),
             InlineKeyboardButton("➕ Savatga qo'sh",     callback_data=f"cart_add_{pid}")],
            [InlineKeyboardButton(cart_label,              callback_data="cart_view")],
        ])
    else:
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ Tugagan", callback_data="noop")
        ]])

    chat_id = update.callback_query.message.chat_id if via_query else update.message.chat_id
    await ctx.bot.send_photo(
        chat_id=chat_id, photo=p[2],
        caption=caption, parse_mode="Markdown", reply_markup=kb
    )

async def back_catalog(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await catalog(update, ctx)

# ═══════════════════════════════════════════════════════════
#  🔍  QIDIRISH
# ═══════════════════════════════════════════════════════════
async def search_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update.effective_user.id)
    await update.message.reply_text(
        t(lang, "search_ask"),
        reply_markup=ReplyKeyboardMarkup([["/bekor"]], resize_keyboard=True)
    )
    return S_QUERY

async def search_start_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang  = get_lang(query.from_user.id)
    await query.message.reply_text(
        t(lang, "search_ask"),
        reply_markup=ReplyKeyboardMarkup([["/bekor"]], resize_keyboard=True)
    )
    return S_QUERY

async def search_query(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang     = get_lang(update.effective_user.id)
    query    = update.message.text.strip()
    products = search_products(query)
    if not products:
        await update.message.reply_text(t(lang, "search_no"), reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    name_col = {"uz": 3, "ru": 4, "en": 5}[lang]
    buttons  = [[InlineKeyboardButton(
        f"{p[name_col]} — {p[6]:,} so'm", callback_data=f"prod_{p[0]}"
    )] for p in products]
    await update.message.reply_text(
        t(lang, "search_found", count=len(products)),
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="Markdown"
    )
    await update.message.reply_text("👇", reply_markup=InlineKeyboardMarkup(buttons))
    return ConversationHandler.END

# ═══════════════════════════════════════════════════════════
#  🛒  BUYURTMA
# ═══════════════════════════════════════════════════════════
async def order_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    pid  = int(query.data.split("_")[1])
    lang = get_lang(query.from_user.id)

    with db() as c:
        p = c.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
    if not p:
        await query.message.reply_text("❌")
        return ConversationHandler.END
    if p[10] == 0:
        await query.message.reply_text("❌ Kechirasiz, mahsulot tugagan!")
        return ConversationHandler.END

    name_col = {"uz": 3, "ru": 4, "en": 5}[lang]
    ctx.user_data.update({
        "o_pid": pid, "o_pname": p[name_col],
        "o_price": p[6], "o_lang": lang, "o_stock": p[10],
        "o_discount": 0, "o_delivery": 0, "o_zone": "", "o_promo": ""
    })
    await query.message.reply_text(
        t(lang, "order_name"),
        reply_markup=ReplyKeyboardMarkup([["/bekor"]], resize_keyboard=True)
    )
    return O_NAME

async def o_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["o_buyer"] = update.message.text.strip()
    lang = ctx.user_data["o_lang"]
    lbl  = {"uz": "Raqamni yuborish", "ru": "Отправить номер", "en": "Send number"}[lang]
    btn  = KeyboardButton(f"📱 {lbl}", request_contact=True)
    await update.message.reply_text(
        t(lang, "order_phone"),
        reply_markup=ReplyKeyboardMarkup([[btn], ["/bekor"]], resize_keyboard=True)
    )
    return O_PHONE

async def o_phone(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["o_phone"] = (
        update.message.contact.phone_number
        if update.message.contact else update.message.text.strip()
    )
    lang = ctx.user_data["o_lang"]
    await update.message.reply_text(
        t(lang, "order_address"),
        reply_markup=ReplyKeyboardMarkup([["/bekor"]], resize_keyboard=True)
    )
    return O_ADDRESS

async def o_address(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["o_addr"] = update.message.text.strip()
    lang = ctx.user_data["o_lang"]
    await update.message.reply_text(
        t(lang, "order_qty"),
        reply_markup=ReplyKeyboardMarkup(
            [["1", "2", "3"], ["5", "10"], ["/bekor"]], resize_keyboard=True
        )
    )
    return O_QTY

async def o_qty(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    if not txt.isdigit() or int(txt) < 1:
        await update.message.reply_text("❌ Raqam kiriting (1 yoki undan ko'p):")
        return O_QTY
    ctx.user_data["o_qty"] = int(txt)
    lang = ctx.user_data["o_lang"]
    await update.message.reply_text(
        t(lang, "order_promo"),
        reply_markup=ReplyKeyboardMarkup([["/skip"], ["/bekor"]], resize_keyboard=True)
    )
    return O_PROMO

async def o_promo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data["o_lang"]
    txt  = update.message.text.strip()
    if txt.lower() in ("/skip", "skip"):
        return await o_ask_zone(update, ctx)
    promo = check_promo(txt)
    if not promo:
        await update.message.reply_text(t(lang, "promo_invalid"))
        return O_PROMO
    subtotal = ctx.user_data["o_price"] * ctx.user_data["o_qty"]
    if promo[2] == "percent":
        discount    = int(subtotal * promo[3] / 100)
        discount_str = f"{promo[3]}%"
    else:
        discount    = min(promo[3], subtotal)
        discount_str = f"{promo[3]:,} so'm"
    ctx.user_data["o_discount"] = discount
    ctx.user_data["o_promo"]    = txt.upper()
    use_promo(txt)
    await update.message.reply_text(t(lang, "promo_applied", discount=discount_str), parse_mode="Markdown")
    return await o_ask_zone(update, ctx)

async def o_ask_zone(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang  = ctx.user_data["o_lang"]
    zones = get_zones(lang)
    buttons = [[InlineKeyboardButton(
        f"📍 {name} — {price:,} so'm", callback_data=f"zone_{zid}"
    )] for zid, name, price in zones]
    await update.message.reply_text(t(lang, "order_zone"), reply_markup=ReplyKeyboardRemove())
    await update.message.reply_text("👇", reply_markup=InlineKeyboardMarkup(buttons))
    return O_ZONE

async def o_zone(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query  = update.callback_query
    await query.answer()
    lang    = ctx.user_data["o_lang"]
    zone_id = int(query.data.split("_")[1])
    zp      = get_zone_price(zone_id)
    zn      = get_zone_name(zone_id, lang)
    ctx.user_data["o_delivery"] = zp
    ctx.user_data["o_zone"]     = zn

    subtotal = ctx.user_data["o_qty"] * ctx.user_data["o_price"]
    discount = ctx.user_data["o_discount"]
    total    = max(0, subtotal - discount) + zp

    user    = get_user(query.from_user.id)
    balance = user[4] if user else 0

    ctx.user_data["o_total_calc"] = total
    # To'lov so'ralmaydi — admin bog'lanadi
    return await save_order_direct(query, ctx)

async def o_use_balance(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query  = update.callback_query
    await query.answer()
    amount = int(query.data.split("_")[1])
    lang   = ctx.user_data["o_lang"]
    ctx.user_data["o_balance_use"] = amount
    ctx.user_data["o_payment"]     = "balance+card"
    remaining = max(0, ctx.user_data["o_total_calc"] - amount)
    await query.message.reply_text(
        t(lang, "balance_used", amount=f"{amount:,}") + "\n\n" +
        t(lang, "card_info", card=CARD_NUMBER, owner=CARD_OWNER, phone=CARD_PHONE, total=f"{remaining:,}"),
        parse_mode="Markdown"
    )
    await query.message.reply_text(t(lang, "send_receipt"))
    return O_RECEIPT

async def o_pay_card(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ctx.user_data["o_payment"] = "card"
    lang  = ctx.user_data["o_lang"]
    total = ctx.user_data.get("o_total_calc", ctx.user_data["o_qty"] * ctx.user_data["o_price"])
    await query.message.reply_text(
        t(lang, "card_info", card=CARD_NUMBER, owner=CARD_OWNER, phone=CARD_PHONE, total=f"{total:,}"),
        parse_mode="Markdown"
    )
    await query.message.reply_text(t(lang, "send_receipt"))
    return O_RECEIPT

async def o_pay_online(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    method = query.data  # pay_click yoki pay_payme
    ctx.user_data["o_payment"] = method.replace("pay_", "")
    lang  = ctx.user_data["o_lang"]
    total = ctx.user_data.get("o_total_calc", ctx.user_data["o_qty"] * ctx.user_data["o_price"])
    pay_name = "Click" if method == "pay_click" else "Payme"
    await query.message.reply_text(
        f"⚡ *{pay_name} orqali to'lash*\n\n"
        f"Quyidagi kartaga o'tkazma qiling:\n\n"
        + t(lang, "card_info", card=CARD_NUMBER, owner=CARD_OWNER, phone=CARD_PHONE, total=f"{total:,}"),
        parse_mode="Markdown"
    )
    await query.message.reply_text(t(lang, "send_receipt"))
    return O_RECEIPT

async def o_receipt(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("❌ Surat yuboring (screenshot yoki foto):")
        return O_RECEIPT
    ctx.user_data["o_receipt"] = update.message.photo[-1].file_id
    return await save_order(update, ctx)

async def save_order(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Buyurtmani saqlaydi, adminga yuboradi — to'lov keyinroq."""
    d    = ctx.user_data
    usr  = update.effective_user
    lang = d["o_lang"]

    bal_use  = d.get("o_balance_use", 0)
    subtotal = d["o_qty"] * d["o_price"]
    discount = d.get("o_discount", 0)
    delivery = d.get("o_delivery", 0)
    total    = max(0, subtotal - discount) + delivery - bal_use
    total    = max(0, total)

    order_id = add_order(
        usr.id, usr.username or "", lang,
        d["o_pid"], d["o_pname"],
        d["o_qty"], d["o_price"],
        d["o_buyer"], d["o_phone"], d["o_addr"],
        "pending",
        discount=discount,
        delivery_price=delivery,
        delivery_zone=d.get("o_zone", ""),
        promo_code=d.get("o_promo", "")
    )

    new_stock = decrease_stock(d["o_pid"], d["o_qty"])
    increment_sold(d["o_pid"], d["o_qty"])

    stock_alert = ""
    if new_stock == 0:
        stock_alert = f"\n🔴 *DIQQAT!* «{d['o_pname']}» *tugadi!*"
    elif new_stock <= LOW_STOCK_THRESHOLD:
        stock_alert = f"\n⚠️ *Qoldiq:* «{d['o_pname']}» — {new_stock} dona"

    admin_text = (
        f"╔══════════════════════════╗\n"
        f"║  🔔  YANGI BUYURTMA #{order_id}   ║\n"
        f"╚══════════════════════════╝\n\n"
        f"📦 *{d['o_pname']}*\n"
        f"🔢 {d['o_qty']} × {d['o_price']:,} = *{subtotal:,} so'm*\n"
        f"🎁 Chegirma: -{discount:,} so'm\n"
        f"🚚 Yetkazish ({d.get('o_zone','—')}): {delivery:,} so'm\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 *Jami: {total:,} so'm*\n"
        f"🎫 Promo: {d.get('o_promo','—')}\n\n"
        f"👤 {d['o_buyer']}\n"
        f"📱 {d['o_phone']}\n"
        f"🏠 {d['o_addr']}\n"
        f"🆔 @{usr.username or '—'} (`{usr.id}`)"
        f"{stock_alert}"
    )
    admin_kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Mijoz bilan bog'lanish", url=f"tg://user?id={usr.id}")],
        [
            InlineKeyboardButton("✅ Tasdiqlash → To'lov yuborish", callback_data=f"oapprove_{order_id}"),
        ],
        [
            InlineKeyboardButton("❌ Bekor qilish", callback_data=f"oreject_{order_id}"),
        ],
    ])
    await ctx.bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown", reply_markup=admin_kb)

    # Foydalanuvchiga xabar
    await update.message.reply_text(
        f"╔══════════════════════╗\n"
        f"║  ✅  BUYURTMA QABUL!  ║\n"
        f"╚══════════════════════╝\n\n"
        f"📦 *{d['o_pname']}* — {d['o_qty']} dona\n"
        f"💰 Jami: *{total:,} so'm*\n\n"
        f"⏳ Admin buyurtmangizni ko'rib chiqmoqda...\n"
        f"📲 Tasdiqlangach, to'lov ma'lumotlari yuboriladi!\n\n"
        f"🆔 Buyurtma raqami: *#{order_id}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🙏 Sabr bilan kuting, tez orada bog'lanamiz!",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


async def save_order_direct(query, ctx: ContextTypes.DEFAULT_TYPE):
    """o_zone dan to'g'ridan-to'g'ri chaqiriladi (inline query versiyasi)."""
    d   = ctx.user_data
    usr = query.from_user
    lang = d["o_lang"]

    discount = d.get("o_discount", 0)
    delivery = d.get("o_delivery", 0)
    subtotal = d["o_qty"] * d["o_price"]
    total    = max(0, subtotal - discount) + delivery

    order_id = add_order(
        usr.id, usr.username or "", lang,
        d["o_pid"], d["o_pname"],
        d["o_qty"], d["o_price"],
        d["o_buyer"], d["o_phone"], d["o_addr"],
        "pending",
        discount=discount,
        delivery_price=delivery,
        delivery_zone=d.get("o_zone", ""),
        promo_code=d.get("o_promo", "")
    )
    decrease_stock(d["o_pid"], d["o_qty"])
    increment_sold(d["o_pid"], d["o_qty"])

    admin_text = (
        f"╔══════════════════════════╗\n"
        f"║  🔔  YANGI BUYURTMA #{order_id}   ║\n"
        f"╚══════════════════════════╝\n\n"
        f"📦 *{d['o_pname']}*\n"
        f"🔢 {d['o_qty']} × {d['o_price']:,} = *{subtotal:,} so'm*\n"
        f"🎁 Chegirma: -{discount:,} so'm\n"
        f"🚚 Yetkazish ({d.get('o_zone','—')}): {delivery:,} so'm\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 *Jami: {total:,} so'm*\n\n"
        f"👤 {d['o_buyer']}\n"
        f"📱 {d['o_phone']}\n"
        f"🏠 {d['o_addr']}\n"
        f"🆔 @{usr.username or '—'} (`{usr.id}`)"
    )
    admin_kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Mijoz bilan bog'lanish", url=f"tg://user?id={usr.id}")],
        [InlineKeyboardButton("✅ Tasdiqlash → To'lov yuborish", callback_data=f"oapprove_{order_id}")],
        [InlineKeyboardButton("❌ Bekor qilish", callback_data=f"oreject_{order_id}")],
    ])
    await ctx.bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown", reply_markup=admin_kb)

    await query.message.reply_text(
        f"╔══════════════════════╗\n"
        f"║  ✅  BUYURTMA QABUL!  ║\n"
        f"╚══════════════════════╝\n\n"
        f"📦 *{d['o_pname']}* — {d['o_qty']} dona\n"
        f"💰 Jami: *{total:,} so'm*\n\n"
        f"⏳ Admin buyurtmangizni ko'rib chiqmoqda...\n"
        f"📲 Tasdiqlangach, to'lov ma'lumotlari yuboriladi!\n\n"
        f"🆔 Buyurtma raqami: *#{order_id}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🙏 Sabr bilan kuting!",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

# ═══════════════════════════════════════════════════════════
#  ⭐  BUYURTMA HOLATI + SHARH
# ═══════════════════════════════════════════════════════════
STATUS_LABEL = {
    "confirmed": "✅ Tasdiqlandi",
    "delivered": "🚚 Yetkazildi",
    "cancelled": "❌ Bekor qilindi",
}

async def order_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID:
        return ConversationHandler.END
    parts    = query.data.split("_", 2)
    order_id = int(parts[1])
    status   = parts[2]
    ctx.user_data["note_order_id"] = order_id
    ctx.user_data["note_status"]   = status
    label = STATUS_LABEL.get(status, status)
    await query.message.reply_text(
        f"📝 *{label}* — buyurtma #{order_id}\n\n"
        f"Mijozga izoh yuboring yoki /skip bosing:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([["/skip"]], resize_keyboard=True, one_time_keyboard=True)
    )
    return ADM_NOTE

async def order_status_note(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    txt      = update.message.text.strip()
    note     = "" if txt.lower() in ("/skip", "skip") else txt
    order_id = ctx.user_data.pop("note_order_id", None)
    status   = ctx.user_data.pop("note_status", None)
    if not order_id or not status:
        await update.message.reply_text("❌ Xatolik.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    update_order_status(order_id, status)
    label = STATUS_LABEL.get(status, status)
    await update.message.reply_text(
        f"✅ #{order_id} buyurtma holati: *{label}*",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    with db() as c:
        order = c.execute(
            "SELECT user_id,lang,product_name,product_id FROM orders WHERE id=?", (order_id,)
        ).fetchone()
    if order:
        user_lang = order[1]
        note_line = f"\n\n💬 *Admin izohi:* {note}" if note else ""
        msg = f"📦 *{order[2]}*\n\n{t(user_lang, f'status_{status}')}{note_line}"
        try:
            await ctx.bot.send_message(order[0], msg, parse_mode="Markdown")
        except Exception:
            pass
        if status == "delivered":
            rate_kb = InlineKeyboardMarkup([[
                InlineKeyboardButton(f"{'⭐'*i} {i}", callback_data=f"rate_{order_id}_{order[3]}_{i}")
                for i in range(1, 6)
            ]])
            try:
                await ctx.bot.send_message(order[0], t(user_lang, "rate_ask"), reply_markup=rate_kb)
            except Exception:
                pass
    return ConversationHandler.END

# ═══════════════════════════════════════════════════════════
#  💳  TO'LOV OQIMI: Admin tasdiqlash → Chek → Tasdiqlash
# ═══════════════════════════════════════════════════════════

async def order_approve(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Admin ✅ Tasdiqlash — foydalanuvchiga to'lov usullarini yuboradi."""
    query = update.callback_query
    await query.answer("✅ Tasdiqlandi!")
    if query.from_user.id != ADMIN_ID:
        return
    oid = int(query.data.split("_")[1])
    update_order_status(oid, "approved")
    with db() as c:
        order = c.execute(
            "SELECT user_id, lang, product_name, total FROM orders WHERE id=?", (oid,)
        ).fetchone()
    if not order:
        await query.message.reply_text("❌ Buyurtma topilmadi.")
        return
    uid, lang, pname, total = order

    # Adminga tasdiq
    await query.message.reply_text(
        f"✅ *#{oid} tasdiqlandi!* Foydalanuvchiga to'lov ma'lumotlari yuborildi.",
        parse_mode="Markdown"
    )

    # Foydalanuvchiga to'lov usullari
    pay_kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 Karta orqali to'lash",  callback_data=f"upay_{oid}_card")],
        [InlineKeyboardButton("⚡ Click orqali to'lash",  callback_data=f"upay_{oid}_click")],
        [InlineKeyboardButton("💚 Payme orqali to'lash",  callback_data=f"upay_{oid}_payme")],
    ])
    try:
        await ctx.bot.send_message(
            uid,
            f"╔══════════════════════════╗\n"
            f"║  🎉  BUYURTMA TASDIQLANDI!  ║\n"
            f"╚══════════════════════════╝\n\n"
            f"📦 *{pname}*\n"
            f"💰 To'lov summasi: *{total:,} so'm*\n\n"
            f"👇 Qulay to'lov usulini tanlang:",
            parse_mode="Markdown",
            reply_markup=pay_kb
        )
    except Exception as e:
        await query.message.reply_text(f"⚠️ Foydalanuvchiga xabar yuborib bo'lmadi: {e}")


async def order_reject(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Admin ❌ Bekor — buyurtma bekor qilinadi."""
    query = update.callback_query
    await query.answer("❌ Bekor qilindi")
    if query.from_user.id != ADMIN_ID:
        return
    oid = int(query.data.split("_")[1])
    update_order_status(oid, "cancelled")
    with db() as c:
        order = c.execute(
            "SELECT user_id, lang, product_name FROM orders WHERE id=?", (oid,)
        ).fetchone()
    await query.message.reply_text(f"❌ *#{oid} bekor qilindi.*", parse_mode="Markdown")
    if order:
        try:
            await ctx.bot.send_message(
                order[0],
                f"╔══════════════════════╗\n"
                f"║  😔  BUYURTMA BEKOR   ║\n"
                f"╚══════════════════════╝\n\n"
                f"📦 *{order[2]}*\n\n"
                f"❌ Afsuski, buyurtmangiz bekor qilindi.\n"
                f"📞 Qo'shimcha ma'lumot uchun adminga murojaat qiling.",
                parse_mode="Markdown"
            )
        except Exception:
            pass


async def user_pay_method(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Foydalanuvchi to'lov usulini tanladi → karta ma'lumotlari + chek so'rash."""
    query = update.callback_query
    await query.answer()
    parts  = query.data.split("_")   # upay_<oid>_<method>
    oid    = int(parts[1])
    method = parts[2]

    with db() as c:
        order = c.execute("SELECT total, product_name FROM orders WHERE id=?", (oid,)).fetchone()
    total = order[0] if order else 0
    pname = order[1] if order else "mahsulot"

    method_icons = {"card": "💳 Karta", "click": "⚡ Click", "payme": "💚 Payme"}
    label = method_icons.get(method, "💳 Karta")

    # PENDING_RECEIPT ga yozamiz
    PENDING_RECEIPT[query.from_user.id] = oid

    await query.message.reply_text(
        f"╔══════════════════════════╗\n"
        f"║   {label} ORQALI TO'LOV   ║\n"
        f"╚══════════════════════════╝\n\n"
        f"📦 *{pname}*\n"
        f"💰 To'lov summasi: *{total:,} so'm*\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏦 *Karta raqami:*\n"
        f"`{CARD_NUMBER}`\n\n"
        f"👤 *Karta egasi:* {CARD_OWNER}\n"
        f"📱 *Telefon:* {CARD_PHONE}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"✅ To'lovni amalga oshiring va\n"
        f"📸 *TO'LOV CHEKINI (screenshot) shu yerga yuboring!*",
        parse_mode="Markdown"
    )


async def receipt_photo_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Foydalanuvchi chek suratini yuboradi — adminga jo'natiladi."""
    uid = update.effective_user.id
    oid = PENDING_RECEIPT.get(uid)
    if not oid:
        # Bu buyurtma bilan bog'liq emas — e'tiborsiz qoldirish
        return

    receipt_id = update.message.photo[-1].file_id
    update_receipt(oid, receipt_id)
    update_order_status(oid, "paid")
    del PENDING_RECEIPT[uid]

    with db() as c:
        order = c.execute(
            "SELECT product_name, total, buyer_name, phone, address FROM orders WHERE id=?", (oid,)
        ).fetchone()
    pname  = order[0] if order else "mahsulot"
    total  = order[1] if order else 0
    bname  = order[2] if order else "—"
    phone  = order[3] if order else "—"
    addr   = order[4] if order else "—"

    # Foydalanuvchiga tasdiqlash
    await update.message.reply_text(
        f"╔══════════════════════════╗\n"
        f"║   🧾  CHEK QABUL QILINDI!  ║\n"
        f"╚══════════════════════════╝\n\n"
        f"✅ Chekingiz admin tekshirishga yuborildi.\n"
        f"⏳ Tekshirilgach, darhol xabar beramiz!\n\n"
        f"🆔 Buyurtma: *#{oid}*",
        parse_mode="Markdown"
    )

    # Adminga chek + tasdiqlash tugmalari
    admin_check_kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Chek qabul — Tasdiqlash!", callback_data=f"ochekok_{oid}")],
        [InlineKeyboardButton("❌ Chek rad etish",           callback_data=f"ochekrad_{oid}")],
        [InlineKeyboardButton("💬 Mijoz bilan bog'lanish",   url=f"tg://user?id={uid}")],
    ])
    admin_caption = (
        f"🧾 *#{oid} BUYURTMA CHEKI KELDI!*\n\n"
        f"📦 {pname}\n"
        f"💰 *{total:,} so'm*\n"
        f"👤 {bname} | 📱 {phone}\n"
        f"🏠 {addr}"
    )
    await ctx.bot.send_photo(
        ADMIN_ID, receipt_id,
        caption=admin_caption,
        parse_mode="Markdown",
        reply_markup=admin_check_kb
    )


async def receipt_ok(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Admin ✅ Chek qabul — foydalanuvchiga muvaffaqiyat xabari."""
    query = update.callback_query
    await query.answer("✅ Chek qabul qilindi!")
    if query.from_user.id != ADMIN_ID:
        return
    oid = int(query.data.split("_")[1])
    update_order_status(oid, "confirmed")

    with db() as c:
        order = c.execute(
            "SELECT user_id, lang, product_name, total, product_id FROM orders WHERE id=?", (oid,)
        ).fetchone()

    # Adminga tasdiq
    await query.message.reply_text(
        f"✅ *#{oid} tasdiqlandi!* Foydalanuvchiga xabar yuborildi. 🎉",
        parse_mode="Markdown"
    )

    if order:
        uid, lang, pname, total, pid = order
        rate_kb = InlineKeyboardMarkup([[
            InlineKeyboardButton(f"{'⭐'*i} {i}", callback_data=f"rate_{oid}_{pid}_{i}")
            for i in range(1, 6)
        ]])
        try:
            await ctx.bot.send_message(
                uid,
                f"╔══════════════════════════╗\n"
                f"║  🎊  TO'LOV TASDIQLANDI!   ║\n"
                f"╚══════════════════════════╝\n\n"
                f"📦 *{pname}*\n"
                f"💰 *{total:,} so'm* — to'landi ✅\n\n"
                f"🚚 Buyurtmangiz yaqin orada\n"
                f"yetkazib beriladi!\n\n"
                f"🆔 Buyurtma: *#{oid}*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🙏 Xarid qilganingiz uchun rahmat!\n"
                f"⭐ Mahsulotga baho bering:",
                parse_mode="Markdown",
                reply_markup=rate_kb
            )
        except Exception:
            pass


async def receipt_reject(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Admin ❌ Chek rad — foydalanuvchiga qayta yuborish so'rovi."""
    query = update.callback_query
    await query.answer("❌ Rad etildi")
    if query.from_user.id != ADMIN_ID:
        return
    oid = int(query.data.split("_")[1])

    with db() as c:
        order = c.execute(
            "SELECT user_id, lang, product_name, total FROM orders WHERE id=?", (oid,)
        ).fetchone()

    await query.message.reply_text(
        f"❌ *#{oid} cheki rad etildi.* Foydalanuvchiga qayta yuborish so'rovi ketdi.",
        parse_mode="Markdown"
    )

    if order:
        uid, lang, pname, total = order
        # Qayta chek yuborishga ruxsat
        PENDING_RECEIPT[uid] = oid
        update_order_status(oid, "approved")
        try:
            await ctx.bot.send_message(
                uid,
                f"╔══════════════════════╗\n"
                f"║  ⚠️  CHEK RAD ETILDI   ║\n"
                f"╚══════════════════════╝\n\n"
                f"📦 *{pname}* — *{total:,} so'm*\n\n"
                f"❌ Yuborgan chekingiz qabul qilinmadi.\n\n"
                f"📸 Iltimos, *to'g'ri to'lov cheki*ni\n"
                f"qaytadan yuboring (aniq screenshot):\n\n"
                f"🏦 Karta: `{CARD_NUMBER}`\n"
                f"👤 Egasi: {CARD_OWNER}",
                parse_mode="Markdown"
            )
        except Exception:
            pass


async def rate_product(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query  = update.callback_query
    await query.answer()
    parts  = query.data.split("_")
    oid, pid, rating = int(parts[1]), int(parts[2]), int(parts[3])
    lang   = get_lang(query.from_user.id)
    ctx.user_data.update({"r_order_id": oid, "r_product_id": pid, "r_rating": rating})
    await query.edit_message_text(f"{'⭐'*rating} — {rating}/5")
    await query.message.reply_text(
        t(lang, "rate_comment"),
        reply_markup=ReplyKeyboardMarkup([["/skip"]], resize_keyboard=True)
    )
    return R_COMMENT

async def rate_comment_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang    = get_lang(update.effective_user.id)
    comment = "" if update.message.text.strip().lower() in ("/skip", "skip") else update.message.text.strip()
    add_review(
        ctx.user_data["r_order_id"],
        update.effective_user.id,
        ctx.user_data["r_product_id"],
        ctx.user_data["r_rating"],
        comment
    )
    await update.message.reply_text(t(lang, "rate_thanks"), reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# ═══════════════════════════════════════════════════════════
#  👥  REFERAL + BALANS
# ═══════════════════════════════════════════════════════════
async def _reply(update, text, kb):
    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(text, reply_markup=kb, parse_mode="Markdown")
            return
        except Exception:
            pass
        await update.callback_query.message.reply_text(text, reply_markup=kb, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=kb, parse_mode="Markdown")

async def referral(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid      = update.effective_user.id
    lang     = get_lang(uid)
    bot_info = await ctx.bot.get_me()
    link     = f"https://t.me/{bot_info.username}?start=ref_{uid}"
    user     = get_user(uid)
    ref_cnt  = user[5] if user else 0
    total_b  = ref_cnt * REFERRAL_BONUS
    kb       = InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menyu", callback_data="menu_home")]])
    await _reply(update, t(lang, "referral_info", link=link, bonus=f"{REFERRAL_BONUS:,}",
                           count=ref_cnt, total=f"{total_b:,}"), kb)

async def balance_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid     = update.effective_user.id
    lang    = get_lang(uid)
    user    = get_user(uid)
    balance = user[4] if user else 0
    kb      = InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menyu", callback_data="menu_home")]])
    await _reply(update, t(lang, "balance_info", balance=f"{balance:,}"), kb)

# ═══════════════════════════════════════════════════════════
#  📋  MIJOZ BUYURTMALARI
# ═══════════════════════════════════════════════════════════
async def my_orders(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid    = update.effective_user.id
    lang   = get_lang(uid)
    orders = get_orders(uid)
    kb     = InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menyu", callback_data="menu_home")]])
    if not orders:
        await _reply(update, t(lang, "no_orders"), kb)
        return
    S = {
        "new": t(lang,"status_new"), "confirmed": t(lang,"status_confirmed"),
        "delivered": t(lang,"status_delivered"), "cancelled": t(lang,"status_cancelled"),
    }
    lines = [
        f"🔹 *#{o[0]}* | {o[5]} | {o[8]:,} so'm | {S.get(o[13],'?')}"
        for o in orders
    ]
    await _reply(update, t(lang, "my_orders") + "\n\n" + "\n".join(lines), kb)

# ═══════════════════════════════════════════════════════════
#  🛠  ADMIN PANEL
# ═══════════════════════════════════════════════════════════
def admin_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Mahsulot qo'shish",  callback_data="adm_addprod"),
         InlineKeyboardButton("✏️ Mahsulot tahrirlash", callback_data="adm_editprod")],
        [InlineKeyboardButton("🗑 Mahsulot o'chirish", callback_data="adm_delprod"),
         InlineKeyboardButton("🔢 Zahira yangilash",   callback_data="adm_stock")],
        [InlineKeyboardButton("⚠️ Kam qolganlar",      callback_data="adm_lowstock"),
         InlineKeyboardButton("🏆 Top sotilganlar",    callback_data="adm_topsales")],
        [InlineKeyboardButton("📊 Statistika",         callback_data="adm_stats"),
         InlineKeyboardButton("📋 Buyurtmalar",        callback_data="adm_orders")],
        [InlineKeyboardButton("📢 Broadcast",          callback_data="adm_broadcast"),
         InlineKeyboardButton("📥 CSV Export",         callback_data="adm_export")],
        [InlineKeyboardButton("🎁 Promo qo'shish",     callback_data="adm_addpromo"),
         InlineKeyboardButton("🎫 Promo ro'yxat",      callback_data="adm_promos")],
        [InlineKeyboardButton("📦 Hudud qo'shish",     callback_data="adm_addzone"),
         InlineKeyboardButton("⭐ Sharhlar",           callback_data="adm_reviews")],
        [InlineKeyboardButton("🏠 Bosh menyu",         callback_data="menu_home")],
    ])

async def admin_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        if update.message:
            await update.message.reply_text("❌ Ruxsat yo'q.")
        return
    text = "🛠 *Admin Panel* — barcha boshqaruvlar:"
    kb = admin_kb()
    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=kb)
    else:
        query = update.callback_query
        try:
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            await query.message.reply_text(text, parse_mode="Markdown", reply_markup=kb)

async def menu_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query  = update.callback_query
    await query.answer()
    action = query.data
    lang   = get_lang(query.from_user.id)

    if action in ("menu_home", "menu_back"):
        await show_main_menu(update, ctx, lang, via_query=True)
    elif action == "menu_catalog":
        await catalog(update, ctx)
    elif action == "menu_orders":
        await my_orders(update, ctx)
    elif action == "menu_balance":
        await balance_cmd(update, ctx)
    elif action == "menu_referral":
        await referral(update, ctx)
    elif action == "menu_lang":
        try:
            await query.edit_message_text(t(lang, "choose_lang"), reply_markup=lang_kb())
        except Exception:
            await query.message.reply_text(t(lang, "choose_lang"), reply_markup=lang_kb())
    elif action == "menu_admin":
        if query.from_user.id == ADMIN_ID:
            await admin_menu(update, ctx)
        else:
            await query.answer("❌ Ruxsat yo'q!", show_alert=True)

async def admin_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query  = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID:
        return
    action = query.data

    if action == "adm_stats":
        tot_o, tot_r, new_o, tot_u, tot_p, avg_r = get_stats()
        await query.message.reply_text(
            f"📊 *Statistika*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👥 Foydalanuvchilar: *{tot_u}*\n"
            f"📦 Faol mahsulotlar: *{tot_p}*\n"
            f"🛒 Jami buyurtmalar: *{tot_o}*\n"
            f"🆕 Yangi (ko'rilmagan): *{new_o}*\n"
            f"💰 Jami daromad: *{tot_r:,} so'm*\n"
            f"⭐ O'rtacha reyting: *{avg_r:.1f}/5*",
            parse_mode="Markdown"
        )

    elif action == "adm_orders":
        orders = get_orders()
        if not orders:
            await query.message.reply_text("😔 Buyurtmalar yo'q.")
            return
        S = {"new":"🆕","confirmed":"✅","delivered":"🚚","cancelled":"❌"}
        lines = [
            f"{S.get(o[13],'?')} *#{o[0]}* | {o[5]} | {o[8]:,} so'm | `{o[11]}`"
            for o in orders
        ]
        await query.message.reply_text(
            "📋 *So'nggi buyurtmalar:*\n\n" + "\n".join(lines),
            parse_mode="Markdown"
        )

    elif action == "adm_delprod":
        products = get_products()
        if not products:
            await query.message.reply_text("😔 Mahsulotlar yo'q.")
            return
        buttons = [[InlineKeyboardButton(
            f"🗑 {p[3]} — #{p[0]}", callback_data=f"delp_{p[0]}"
        )] for p in products]
        await query.message.reply_text(
            "🗑 *Qaysi mahsulotni o'chirish?*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif action == "adm_stock":
        products = get_products()
        if not products:
            await query.message.reply_text("😔 Mahsulotlar yo'q.")
            return
        buttons = [[InlineKeyboardButton(
            f"📦 {p[3]} — {p[10]} dona", callback_data=f"setstock_{p[0]}"
        )] for p in products]
        await query.message.reply_text(
            "🔢 *Qaysi mahsulot zahirasini yangilash?*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif action == "adm_lowstock":
        items = get_low_stock()
        if not items:
            await query.message.reply_text("✅ Barcha mahsulot zahirasi yetarli!")
            return
        lines = [f"⚠️ #{p[0]} *{p[1]}* — {p[2]} dona" for p in items]
        await query.message.reply_text(
            "⚠️ *Kam qolgan mahsulotlar:*\n\n" + "\n".join(lines),
            parse_mode="Markdown"
        )

    elif action == "adm_topsales":
        tops = get_top_products(10)
        if not tops:
            await query.message.reply_text("😔 Hali sotuv ma'lumoti yo'q.")
            return
        medals = ["🥇", "🥈", "🥉"]
        lines  = []
        for i, p in enumerate(tops):
            m = medals[i] if i < 3 else f"{i+1}."
            lines.append(
                f"{m} *{p[1]}*\n"
                f"   🛒 {p[2]:,} dona  |  👁 {p[3]:,} ko'rishlar  |  💰 {p[4]:,} so'm"
            )
        await query.message.reply_text(
            "🏆 *Eng ko'p sotilganlar:*\n\n" + "\n\n".join(lines),
            parse_mode="Markdown"
        )

    elif action == "adm_promos":
        promos = get_promo_codes()
        if not promos:
            await query.message.reply_text("😔 Promo-kodlar yo'q.")
            return
        lines = []
        for p in promos:
            status   = '✅' if p[6] else '❌'
            discount = f"{p[3]}%" if p[2] == 'percent' else f"{p[3]} som"
            lines.append(f"{status} *{p[1]}* — {discount} ({p[5]}/{p[4]} ta ishlatilgan)")

        await query.message.reply_text("\n".join(lines), parse_mode="Markdown")

    elif action == "adm_reviews":
        with db() as c:
            reviews = c.execute(
                "SELECT r.rating,r.comment,p.name_uz "
                "FROM reviews r LEFT JOIN products p ON r.product_id=p.id "
                "ORDER BY r.id DESC LIMIT 15"
            ).fetchall()
        if not reviews:
            await query.message.reply_text("😔 Sharhlar yo'q.")
            return
        lines = [f"{'⭐'*r[0]} *{r[2]}* — {r[1] or '(izohsiz)'}" for r in reviews]
        await query.message.reply_text("\n".join(lines), parse_mode="Markdown")

    elif action == "adm_export":
        orders = get_orders()
        if not orders:
            await query.message.reply_text("😔 Hali buyurtma yo'q.")
            return
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID","Foydalanuvchi","Mahsulot","Miqdor","Narx","Jami","Ism","Telefon","Manzil","To'lov","Status","Sana"])
        for o in orders:
            writer.writerow([
                o[0], f"@{o[2]}" if o[2] else str(o[1]),
                o[5], o[6], f"{o[7]:,}", f"{o[8]:,}",
                o[9], o[10], o[11], o[12], o[13],
                o[19][:16].replace("T"," ") if o[19] else ""
            ])
        content = output.getvalue().encode("utf-8-sig")
        bio = io.BytesIO(content)
        bio.name = f"buyurtmalar_{datetime.now().strftime('%d%m%Y_%H%M')}.csv"
        await query.message.reply_document(
            bio,
            caption=f"📊 *Buyurtmalar ro'yxati*\nJami: {len(orders)} ta",
            parse_mode="Markdown"
        )

    elif action == "adm_editprod":
        products = get_products()
        if not products:
            await query.message.reply_text("😔 Mahsulotlar yo'q.")
            return
        buttons = [[InlineKeyboardButton(
            f"✏️ {p[3]} — #{p[0]}", callback_data=f"editp_{p[0]}"
        )] for p in products]
        await query.message.reply_text(
            "✏️ *Qaysi mahsulotni tahrirlash?*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif action == "adm_addprod":
        # Mahsulot qo'shish: kategoriya tanlash (ConversationHandler entry point)
        cats    = CATEGORIES["uz"]
        buttons = [[InlineKeyboardButton(name, callback_data=f"acat_{key}")]
                   for name, key in zip(cats, CAT_KEYS)]
        await query.message.reply_text(
            "📂 *Kategoriyani tanlang:*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

# ═══════════════════════════════════════════════════════════
#  ➕  ADMIN: MAHSULOT QO'SHISH (ConversationHandler)
# ═══════════════════════════════════════════════════════════
async def ap_cat(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Kategoriya tanlandi → surat so'raladi."""
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID:
        return ConversationHandler.END
    ctx.user_data["ap_cat"] = query.data.split("_", 1)[1]
    await query.message.reply_text(
        "🖼 *Mahsulot suratini yuboring:*",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([["/bekor"]], resize_keyboard=True)
    )
    return AP_PHOTO

async def ap_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("❌ Surat yuboring (rasm sifatida):")
        return AP_PHOTO
    ctx.user_data["ap_photo"] = update.message.photo[-1].file_id
    await update.message.reply_text(
        "✏️ *Mahsulot nomini kiriting:*\n_(O'zbek tilida)_",
        parse_mode="Markdown"
    )
    return AP_NAME

async def ap_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["ap_name"] = update.message.text.strip()
    await update.message.reply_text(
        "💰 *Narxini kiriting (so'mda):*\n_Faqat raqam, masalan: 150000_",
        parse_mode="Markdown"
    )
    return AP_PRICE

async def ap_price(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip().replace(" ", "").replace(",", "")
    if not txt.isdigit():
        await update.message.reply_text("❌ Faqat raqam kiriting (masalan: 150000):")
        return AP_PRICE
    ctx.user_data["ap_price"] = int(txt)
    await update.message.reply_text(
        "📝 *Tavsifini kiriting:*\n_(Qisqacha ma'lumot)_",
        parse_mode="Markdown"
    )
    return AP_DESC

async def ap_desc(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["ap_desc"] = update.message.text.strip()
    await update.message.reply_text(
        "📦 *Ombordagi miqdorini kiriting:*\n_Masalan: 50 (cheklanmagan bo'lsa 9999)_",
        parse_mode="Markdown"
    )
    return AP_STOCK

async def ap_stock(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    if not txt.isdigit() or int(txt) < 0:
        await update.message.reply_text("❌ Faqat musbat raqam kiriting:")
        return AP_STOCK

    d    = ctx.user_data
    pid  = add_product(
        d["ap_cat"], d["ap_photo"],
        d["ap_name"], d["ap_price"], d["ap_desc"],
        stock=int(txt)
    )

    # ──── KANALGA AVTOMATIK POST ────────────────────────────
    try:
        bot_info = await ctx.bot.get_me()
        qty_val  = int(txt)
        if qty_val > 10:
            stock_line = f"🟢 Mavjud: *{qty_val} dona*"
        elif qty_val > 3:
            stock_line = f"🟡 Mavjud: *{qty_val} dona* — oz qoldi!"
        else:
            stock_line = f"🔴 Mavjud: *{qty_val} dona* — tez tugaydi!"

        caption = (
            f"🆕 *YANGI MAHSULOT*\n\n"
            f"🌟 *{d['ap_name']}*\n\n"
            f"💰 Narxi: *{d['ap_price']:,} so'm*\n"
            f"{stock_line}\n\n"
            f"📝 {d['ap_desc']}\n\n"
            f"🔥 Tez buyurtma bering!"
        )
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                "🛒 Buyurtma berish",
                url=f"https://t.me/{bot_info.username}?start=product_{pid}"
            )
        ]])
        await ctx.bot.send_photo(
            chat_id=CHANNEL_ID, photo=d["ap_photo"],
            caption=caption, parse_mode="Markdown", reply_markup=kb
        )
        channel_status = f"✅ Kanalga yuborildi"
    except Exception as e:
        channel_status = f"⚠️ Kanal xatosi: {e}"

    lang = get_lang(update.effective_user.id)
    await update.message.reply_text(
        f"✅ *{d['ap_name']}* qo'shildi!\n\n"
        f"💰 {d['ap_price']:,} so'm  📦 {txt} dona  🆔 #{pid}\n\n"
        f"{channel_status}",
        parse_mode="Markdown",
        reply_markup=main_menu_kb(update.effective_user.id, lang)
    )
    return ConversationHandler.END

# ═══════════════════════════════════════════════════════════
#  🎁  ADMIN: PROMO-KOD QO'SHISH
# ═══════════════════════════════════════════════════════════
async def adm_promo_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Entry point: callback query 'adm_addpromo'"""
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID:
        return ConversationHandler.END
    await query.message.reply_text(
        "🎁 *Promo-kod nomini kiriting:*\n_(Masalan: SALE20)_",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([["/bekor"]], resize_keyboard=True)
    )
    return ADM_PROMO_CODE

async def adm_promo_code(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["new_promo_code"] = update.message.text.strip().upper()
    await update.message.reply_text(
        "📊 *Chegirma turini tanlang:*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("% Foiz",       callback_data="promotype_percent"),
             InlineKeyboardButton("💰 Summa (so'm)", callback_data="promotype_amount")]
        ])
    )
    return ADM_PROMO_TYPE

async def adm_promo_type(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ctx.user_data["new_promo_type"] = query.data.split("_")[1]
    lbl = "foiz (masalan 15)" if ctx.user_data["new_promo_type"] == "percent" else "so'm (masalan 10000)"
    await query.message.reply_text(f"💰 Chegirma miqdorini kiriting ({lbl}):")
    return ADM_PROMO_VAL

async def adm_promo_val(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    if not txt.isdigit():
        await update.message.reply_text("❌ Faqat raqam kiriting:")
        return ADM_PROMO_VAL
    ctx.user_data["new_promo_val"] = int(txt)
    await update.message.reply_text("🔢 Maksimal ishlatilish soni (masalan: 100):")
    return ADM_PROMO_MAX

async def adm_promo_max(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    if not txt.isdigit():
        await update.message.reply_text("❌ Faqat raqam kiriting:")
        return ADM_PROMO_MAX
    code = ctx.user_data["new_promo_code"]
    ok   = add_promo_code(code, ctx.user_data["new_promo_type"],
                          ctx.user_data["new_promo_val"], int(txt))
    if ok:
        await update.message.reply_text(
            f"✅ Promo-kod *{code}* qo'shildi!",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        await update.message.reply_text("❌ Bu kod allaqachon mavjud!", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# ═══════════════════════════════════════════════════════════
#  📢  ADMIN: BROADCAST
# ═══════════════════════════════════════════════════════════
async def adm_broadcast_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Entry point: callback query 'adm_broadcast'"""
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID:
        return ConversationHandler.END
    await query.message.reply_text(
        "📢 *Barcha foydalanuvchilarga xabar yozing:*",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([["/bekor"]], resize_keyboard=True)
    )
    return ADM_BROADCAST

async def adm_broadcast_msg(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    with db() as c:
        users = c.execute("SELECT user_id FROM users").fetchall()
    sent = failed = 0
    for (uid,) in users:
        try:
            await ctx.bot.send_message(uid, f"📢 *E'lon!*\n\n{text}", parse_mode="Markdown")
            sent += 1
        except Exception:
            failed += 1
    await update.message.reply_text(
        f"✅ Yuborildi: *{sent}* ta\n❌ Xatolik: *{failed}* ta",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

# ═══════════════════════════════════════════════════════════
#  📦  ADMIN: HUDUD QO'SHISH
# ═══════════════════════════════════════════════════════════
async def adm_zone_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Entry point: callback query 'adm_addzone'"""
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID:
        return ConversationHandler.END
    await query.message.reply_text(
        "📦 *Yangi hudud nomini kiriting:*\n_(O'zbek tilida)_",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([["/bekor"]], resize_keyboard=True)
    )
    return ADM_ZONE_NAME_UZ

async def adm_zone_uz(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["new_zone_uz"] = update.message.text.strip()
    await update.message.reply_text("✏️ Hudud nomi *(Rus tilida)*:", parse_mode="Markdown")
    return ADM_ZONE_NAME_RU

async def adm_zone_ru(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["new_zone_ru"] = update.message.text.strip()
    await update.message.reply_text("✏️ Hudud nomi *(Ingliz tilida)*:", parse_mode="Markdown")
    return ADM_ZONE_NAME_EN

async def adm_zone_en(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["new_zone_en"] = update.message.text.strip()
    await update.message.reply_text("💰 Yetkazib berish narxi *(so'mda)*:", parse_mode="Markdown")
    return ADM_ZONE_PRICE

async def adm_zone_price(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    if not txt.isdigit():
        await update.message.reply_text("❌ Faqat raqam kiriting:")
        return ADM_ZONE_PRICE
    with db() as c:
        c.execute(
            "INSERT INTO delivery_zones(name_uz,name_ru,name_en,price) VALUES(?,?,?,?)",
            (ctx.user_data["new_zone_uz"], ctx.user_data["new_zone_ru"],
             ctx.user_data["new_zone_en"], int(txt))
        )
    await update.message.reply_text(
        f"✅ *{ctx.user_data['new_zone_uz']}* hududi qo'shildi!",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

# ═══════════════════════════════════════════════════════════
#  🔢  ADMIN: ZAHIRA YANGILASH
# ═══════════════════════════════════════════════════════════
async def adm_stock_select(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID:
        return ConversationHandler.END
    pid = int(query.data.split("_")[1])
    with db() as c:
        p = c.execute("SELECT name_uz,stock FROM products WHERE id=?", (pid,)).fetchone()
    if not p:
        await query.message.reply_text("❌ Mahsulot topilmadi.")
        return ConversationHandler.END
    ctx.user_data["stock_pid"] = pid
    await query.message.reply_text(
        f"📦 *{p[0]}*\n"
        f"Hozirgi zahira: *{p[1]} dona*\n\n"
        f"Yangi miqdorni kiriting:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([["/bekor"]], resize_keyboard=True)
    )
    return ADM_STOCK_QTY

async def adm_stock_qty(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    if not txt.isdigit() or int(txt) < 0:
        await update.message.reply_text("❌ Faqat musbat raqam kiriting:")
        return ADM_STOCK_QTY
    pid = ctx.user_data["stock_pid"]
    qty = int(txt)
    set_stock(pid, qty)
    with db() as c:
        name = c.execute("SELECT name_uz FROM products WHERE id=?", (pid,)).fetchone()[0]
    status = "✅ faol" if qty > 0 else "❌ yopiq"
    await update.message.reply_text(
        f"✅ *{name}* zahirasi yangilandi!\n"
        f"📦 Yangi miqdor: *{qty} dona*\n"
        f"Holat: {status}",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

# ═══════════════════════════════════════════════════════════
#  🗑  MAHSULOT O'CHIRISH
# ═══════════════════════════════════════════════════════════
async def delete_product_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID:
        return
    pid = int(query.data.split("_")[1])
    with db() as c:
        p = c.execute("SELECT name_uz FROM products WHERE id=?", (pid,)).fetchone()
    delete_product(pid)
    name = p[0] if p else f"#{pid}"
    await query.message.reply_text(f"🗑 *{name}* o'chirildi!", parse_mode="Markdown")

# ═══════════════════════════════════════════════════════════
#  ✏️  ADMIN: MAHSULOT TAHRIRLASH
# ═══════════════════════════════════════════════════════════
async def ep_select(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Mahsulot tanlandi → qaysi maydonni o'zgartirish so'raladi."""
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID:
        return ConversationHandler.END
    pid = int(query.data.split("_")[1])
    ctx.user_data["ep_pid"] = pid
    with db() as c:
        p = c.execute("SELECT name_uz, price, desc_uz, stock FROM products WHERE id=?", (pid,)).fetchone()
    if not p:
        await query.message.reply_text("❌ Mahsulot topilmadi.")
        return ConversationHandler.END
    ctx.user_data["ep_product"] = p
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"📝 Nomi: {p[0][:20]}",       callback_data="epfield_name_uz")],
        [InlineKeyboardButton(f"💰 Narxi: {p[1]:,} so'm",     callback_data="epfield_price")],
        [InlineKeyboardButton(f"📋 Tavsif: {p[2][:20]}...",   callback_data="epfield_desc_uz")],
        [InlineKeyboardButton(f"📦 Zahira: {p[3]} dona",      callback_data="epfield_stock")],
        [InlineKeyboardButton("❌ Bekor",                      callback_data="noop")],
    ])
    await query.message.reply_text(
        f"✏️ *#{pid} mahsulotni tahrirlash*\nQaysi maydonni o'zgartirmoqchisiz?",
        parse_mode="Markdown", reply_markup=kb
    )
    return EP_FIELD

async def ep_field(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Maydon tanlandi → yangi qiymat so'raladi."""
    query = update.callback_query
    await query.answer()
    field = query.data.replace("epfield_", "")
    ctx.user_data["ep_field"] = field
    labels = {"name_uz": "Yangi nomi", "price": "Yangi narxi (raqam)", "desc_uz": "Yangi tavsifi", "stock": "Yangi zahira (raqam)"}
    await query.message.reply_text(
        f"✏️ {labels.get(field, field)} ni kiriting:",
        reply_markup=ReplyKeyboardMarkup([["/bekor"]], resize_keyboard=True)
    )
    return EP_VALUE

async def ep_value(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Yangi qiymat kiritildi → DB yangilanadi."""
    txt   = update.message.text.strip()
    pid   = ctx.user_data.get("ep_pid")
    field = ctx.user_data.get("ep_field")
    if field in ("price", "stock"):
        if not txt.isdigit():
            await update.message.reply_text("❌ Faqat raqam kiriting:")
            return EP_VALUE
        value = int(txt)
    else:
        value = txt
    update_product_field(pid, field, value)
    labels = {"name_uz": "Nomi", "price": "Narxi", "desc_uz": "Tavsifi", "stock": "Zahira"}
    await update.message.reply_text(
        f"✅ *#{pid} mahsulot yangilandi!*\n{labels.get(field,'Maydon')}: *{value}*",
        parse_mode="Markdown", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


# ═══════════════════════════════════════════════════════════
#  🛒  SAVAT (KORZINKA)
# ═══════════════════════════════════════════════════════════
async def cart_add(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Mahsulotni savatga qo'shish."""
    query = update.callback_query
    await query.answer()
    pid  = int(query.data.split("_")[2])
    cart = ctx.user_data.setdefault("cart", {})
    with db() as c:
        p = c.execute("SELECT id, name_uz, price, stock FROM products WHERE id=? AND active=1", (pid,)).fetchone()
    if not p:
        await query.answer("❌ Mahsulot topilmadi!", show_alert=True)
        return
    stock = p[3]
    cur_qty = cart.get(pid, {}).get("qty", 0)
    if cur_qty >= stock:
        await query.answer(f"⚠️ Faqat {stock} dona mavjud!", show_alert=True)
        return
    if pid in cart:
        cart[pid]["qty"] += 1
    else:
        cart[pid] = {"name": p[1], "price": p[2], "qty": 1}
    total_items = sum(v["qty"] for v in cart.values())
    await query.answer(f"✅ Savatga qo'shildi! ({total_items} ta)", show_alert=False)
    await query.message.reply_text(
        f"✅ *{p[1]}* savatga qo'shildi!\n"
        f"🛒 Savatingizda: {total_items} ta mahsulot",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(f"🛒 Savatni ko'rish ({total_items} ta)", callback_data="cart_view")
        ]])
    )

async def cart_view(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Savatni ko'rsatish."""
    query = update.callback_query
    await query.answer()
    cart = ctx.user_data.get("cart", {})
    if not cart:
        await query.message.reply_text(
            "🛒 *Savat bo'sh*\n\nKatalogdan mahsulot qo'shing!",
            parse_mode="Markdown"
        )
        return
    lines  = []
    total  = 0
    for pid, item in cart.items():
        subtotal = item["price"] * item["qty"]
        total   += subtotal
        lines.append(f"• *{item['name']}* × {item['qty']} = {subtotal:,} so'm")
    text = (
        "╔══════════════════════╗\n"
        "║     🛒  SAVATINGIZ     ║\n"
        "╚══════════════════════╝\n\n"
        + "\n".join(lines) +
        f"\n\n━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 *Jami: {total:,} so'm*"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Buyurtma berish",  callback_data="cart_checkout")],
        [InlineKeyboardButton("🗑 Savatni tozalash", callback_data="cart_clear")],
        [InlineKeyboardButton("🛍 Katalogga qaytish", callback_data="menu_catalog")],
    ])
    await query.message.reply_text(text, parse_mode="Markdown", reply_markup=kb)

async def cart_clear(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ctx.user_data["cart"] = {}
    await query.message.reply_text("🗑 *Savat tozalandi.*", parse_mode="Markdown")

async def cart_view_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Savat — /savat buyrug'i orqali ko'rish."""
    cart = ctx.user_data.get("cart", {})
    if not cart:
        await update.message.reply_text(
            "🛒 *Savat hozircha bo'sh*\n\nKatalogga o'ting va mahsulotlarni ➕ Savatga qo'shing!",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛍 Katalog", callback_data="menu_catalog")]])
        )
        return
    lines = []
    total = 0
    for pid, item in cart.items():
        subtotal = item["price"] * item["qty"]
        total   += subtotal
        lines.append(f"• *{item['name']}* × {item['qty']} = {subtotal:,} so'm")
    text = (
        "╔══════════════════════╗\n"
        "║     🛒  SAVATINGIZ     ║\n"
        "╚══════════════════════╝\n\n"
        + "\n".join(lines) +
        f"\n\n━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 *Jami: {total:,} so'm*"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Buyurtma berish",   callback_data="cart_checkout")],
        [InlineKeyboardButton("🗑 Savatni tozalash",  callback_data="cart_clear")],
        [InlineKeyboardButton("🛍 Katalogga qaytish", callback_data="menu_catalog")],
    ])
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=kb)

async def cart_checkout_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Savatdan buyurtma berish — ism so'rash."""
    query = update.callback_query
    await query.answer()
    cart = ctx.user_data.get("cart", {})
    if not cart:
        await query.message.reply_text("🛒 Savat bo'sh!")
        return ConversationHandler.END
    lang = get_lang(query.from_user.id)
    ctx.user_data["co_lang"] = lang
    await query.message.reply_text(
        "📝 *Buyurtma uchun ma'lumotlar*\n\nIsm-familiyangizni kiriting:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([["/bekor"]], resize_keyboard=True)
    )
    return CART_NAME

async def cart_co_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["co_name"] = update.message.text.strip()
    kb = ReplyKeyboardMarkup(
        [[KeyboardButton("📱 Raqamni yuborish", request_contact=True)], ["/bekor"]],
        resize_keyboard=True, one_time_keyboard=True
    )
    await update.message.reply_text("📱 Telefon raqamingizni yuboring:", reply_markup=kb)
    return CART_PHONE

async def cart_co_phone(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.message.contact:
        ctx.user_data["co_phone"] = update.message.contact.phone_number
    else:
        ctx.user_data["co_phone"] = update.message.text.strip()
    await update.message.reply_text(
        "🏠 Yetkazib berish manzilingizni kiriting:",
        reply_markup=ReplyKeyboardMarkup([["/bekor"]], resize_keyboard=True)
    )
    return CART_ADDR

async def cart_co_addr(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Manzil kiritildi → buyurtma saqlanadi, admin xabardor qilinadi."""
    ctx.user_data["co_addr"] = update.message.text.strip()
    usr  = update.effective_user
    cart = ctx.user_data.get("cart", {})
    d    = ctx.user_data
    total = sum(v["price"] * v["qty"] for v in cart.values())
    d["co_total"] = total

    order_ids = []
    for pid, item in cart.items():
        oid = add_order(
            usr.id, usr.username or "", d.get("co_lang", "uz"),
            pid, item["name"],
            item["qty"], item["price"],
            d["co_name"], d["co_phone"], d["co_addr"],
            "pending",
        )
        decrease_stock(pid, item["qty"])
        increment_sold(pid, item["qty"])
        order_ids.append(oid)

    ids_str = ", ".join(f"#{i}" for i in order_ids)

    await update.message.reply_text(
        f"✅ *Buyurtmangiz qabul qilindi!*\n\n"
        f"🆔 Raqam(lar): *{ids_str}*\n"
        f"💰 Jami: *{total:,} so'm*\n\n"
        f"📞 Admin tez orada siz bilan bog'lanadi va to'lov usulini kelishib oladi!\n\n"
        f"Rahmat! 🙏",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )

    # Adminga xabar
    items_txt = "\n".join(
        f"  • {v['name']} × {v['qty']} = {v['price'] * v['qty']:,} so'm"
        for v in cart.values()
    )
    admin_text = (
        f"🛒 *YANGI SAVAT BUYURTMASI!*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{items_txt}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 *Jami: {total:,} so'm*\n\n"
        f"👤 Ism: {d['co_name']}\n"
        f"📱 Tel: {d['co_phone']}\n"
        f"🏠 Manzil: {d['co_addr']}\n"
        f"🆔 Buyurtmalar: {ids_str}\n\n"
        f"⚠️ To'lov hali amalga oshirilmagan — mijoz bilan bog'laning!"
    )
    admin_kb_cart = InlineKeyboardMarkup([[
        InlineKeyboardButton("💬 Mijoz bilan bog'lanish", url=f"tg://user?id={usr.id}")
    ]])
    await ctx.bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown", reply_markup=admin_kb_cart)
    ctx.user_data["cart"] = {}
    return ConversationHandler.END


# ═══════════════════════════════════════════════════════════
#  🔧  YORDAMCHILAR
# ═══════════════════════════════════════════════════════════
async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update.effective_user.id)
    await update.message.reply_text(t(lang, "cancel"), reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def noop(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()

# ═══════════════════════════════════════════════════════════
#  ⏰  SCHEDULED JOBS
# ═══════════════════════════════════════════════════════════
async def check_stuck_orders_job(context):
    stuck = get_stuck_orders(hours=2)
    if not stuck:
        return
    lines = []
    for o in stuck:
        created = o[4][:16].replace("T", " ")
        lines.append(f"🔴 *#{o[0]}* | {o[1]} | {o[2]} | `{o[3]}` | {created}")
    await context.bot.send_message(
        ADMIN_ID,
        "⏰ *Kutilayotgan buyurtmalar!*\n"
        "2+ soatdan beri ko'rib chiqilmagan:\n\n" + "\n".join(lines),
        parse_mode="Markdown"
    )

async def daily_report_job(context):
    o_today, r_today, u_today = get_today_stats()
    tot_o, tot_r, new_o, tot_u, tot_p, avg_r = get_stats()
    low = get_low_stock()
    low_str = ""
    if low:
        low_str = "\n\n⚠️ *Kam qolgan mahsulotlar:*\n" + "\n".join(
            [f"  • {p[1]} — {p[2]} dona" for p in low]
        )
    await context.bot.send_message(
        ADMIN_ID,
        f"🌅 *Kunlik hisobot — {datetime.now().strftime('%d.%m.%Y')}*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 Bugungi buyurtmalar: *{o_today}*\n"
        f"💰 Bugungi daromad: *{r_today:,} so'm*\n"
        f"👥 Yangi mijozlar: *{u_today}*\n\n"
        f"📊 *Umumiy:*\n"
        f"  Jami buyurtmalar: {tot_o}\n"
        f"  Jami daromad: {tot_r:,} so'm\n"
        f"  🆕 Yangi (ko'rilmagan): {new_o}\n"
        f"  Foydalanuvchilar: {tot_u}\n"
        f"  Faol mahsulotlar: {tot_p}"
        f"{low_str}",
        parse_mode="Markdown"
    )

# ═══════════════════════════════════════════════════════════
#  🚀  MAIN
# ═══════════════════════════════════════════════════════════
def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN muhit o'zgaruvchisi o'rnatilmagan!")
    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # ── Mahsulot qo'shish ──────────────────────────────────
    add_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(ap_cat, pattern=r"^acat_")],
        states={
            AP_PHOTO: [MessageHandler(filters.PHOTO, ap_photo)],
            AP_NAME:  [MessageHandler(filters.TEXT & ~filters.COMMAND, ap_name)],
            AP_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ap_price)],
            AP_DESC:  [MessageHandler(filters.TEXT & ~filters.COMMAND, ap_desc)],
            AP_STOCK: [MessageHandler(filters.TEXT & ~filters.COMMAND, ap_stock)],
        },
        fallbacks=[CommandHandler("bekor", cancel)],
        allow_reentry=True,
    )

    # ── Buyurtma ───────────────────────────────────────────
    order_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(order_start, pattern=r"^order_\d+$")],
        states={
            O_NAME:    [MessageHandler(filters.TEXT & ~filters.COMMAND, o_name)],
            O_PHONE:   [MessageHandler(filters.CONTACT | (filters.TEXT & ~filters.COMMAND), o_phone)],
            O_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, o_address)],
            O_QTY:     [MessageHandler(filters.TEXT & ~filters.COMMAND, o_qty)],
            O_PROMO:   [
                MessageHandler(filters.TEXT & ~filters.COMMAND, o_promo),
                CommandHandler("skip", o_promo),
            ],
            O_ZONE:    [CallbackQueryHandler(o_zone, pattern=r"^zone_\d+$")],
            O_PAY:     [
                CallbackQueryHandler(o_pay_card,    pattern="^pay_card$"),
                CallbackQueryHandler(o_pay_online,  pattern=r"^pay_(click|payme)$"),
                CallbackQueryHandler(o_use_balance, pattern=r"^usebalance_\d+$"),
            ],
            O_RECEIPT: [MessageHandler(filters.PHOTO, o_receipt)],
        },
        fallbacks=[CommandHandler("bekor", cancel)],
        allow_reentry=True,
    )

    # ── Qidirish ───────────────────────────────────────────
    search_conv = ConversationHandler(
        entry_points=[
            CommandHandler("search", search_start),
            CallbackQueryHandler(search_start_cb, pattern="^menu_search$"),
        ],
        states={
            S_QUERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_query)],
        },
        fallbacks=[CommandHandler("bekor", cancel)],
        allow_reentry=True,
    )

    # ── Sharh ──────────────────────────────────────────────
    review_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(rate_product, pattern=r"^rate_\d+_\d+_\d+$")],
        states={
            R_COMMENT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, rate_comment_handler),
                CommandHandler("skip", rate_comment_handler),
            ],
        },
        fallbacks=[CommandHandler("bekor", cancel)],
        allow_reentry=True,
    )

    # ── Admin: promo-kod ───────────────────────────────────
    promo_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(adm_promo_start, pattern="^adm_addpromo$")],
        states={
            ADM_PROMO_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, adm_promo_code)],
            ADM_PROMO_TYPE: [CallbackQueryHandler(adm_promo_type, pattern=r"^promotype_")],
            ADM_PROMO_VAL:  [MessageHandler(filters.TEXT & ~filters.COMMAND, adm_promo_val)],
            ADM_PROMO_MAX:  [MessageHandler(filters.TEXT & ~filters.COMMAND, adm_promo_max)],
        },
        fallbacks=[CommandHandler("bekor", cancel)],
        allow_reentry=True,
    )

    # ── Admin: broadcast ───────────────────────────────────
    broadcast_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(adm_broadcast_start, pattern="^adm_broadcast$")],
        states={
            ADM_BROADCAST: [MessageHandler(filters.TEXT & ~filters.COMMAND, adm_broadcast_msg)],
        },
        fallbacks=[CommandHandler("bekor", cancel)],
        allow_reentry=True,
    )

    # ── Admin: hudud qo'shish ──────────────────────────────
    zone_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(adm_zone_start, pattern="^adm_addzone$")],
        states={
            ADM_ZONE_NAME_UZ: [MessageHandler(filters.TEXT & ~filters.COMMAND, adm_zone_uz)],
            ADM_ZONE_NAME_RU: [MessageHandler(filters.TEXT & ~filters.COMMAND, adm_zone_ru)],
            ADM_ZONE_NAME_EN: [MessageHandler(filters.TEXT & ~filters.COMMAND, adm_zone_en)],
            ADM_ZONE_PRICE:   [MessageHandler(filters.TEXT & ~filters.COMMAND, adm_zone_price)],
        },
        fallbacks=[CommandHandler("bekor", cancel)],
        allow_reentry=True,
    )

    # ── Admin: zahira yangilash ────────────────────────────
    stock_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(adm_stock_select, pattern=r"^setstock_\d+$")],
        states={
            ADM_STOCK_QTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, adm_stock_qty)],
        },
        fallbacks=[CommandHandler("bekor", cancel)],
        allow_reentry=True,
    )

    # ── Admin: buyurtma holati + izoh ──────────────────────
    note_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(order_status, pattern=r"^ostatus_")],
        states={
            ADM_NOTE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, order_status_note),
                CommandHandler("skip", order_status_note),
            ],
        },
        fallbacks=[CommandHandler("bekor", cancel)],
        allow_reentry=True,
    )

    # ── Admin: mahsulot tahrirlash ─────────────────────────
    edit_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(ep_select, pattern=r"^editp_\d+$")],
        states={
            EP_FIELD: [CallbackQueryHandler(ep_field, pattern=r"^epfield_")],
            EP_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ep_value)],
        },
        fallbacks=[CommandHandler("bekor", cancel)],
        allow_reentry=True,
    )

    # ── Savat (korzinka) checkout ──────────────────────────
    cart_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(cart_checkout_start, pattern="^cart_checkout$")],
        states={
            CART_NAME:  [MessageHandler(filters.TEXT & ~filters.COMMAND, cart_co_name)],
            CART_PHONE: [MessageHandler(filters.CONTACT | (filters.TEXT & ~filters.COMMAND), cart_co_phone)],
            CART_ADDR:  [MessageHandler(filters.TEXT & ~filters.COMMAND, cart_co_addr)],
        },
        fallbacks=[CommandHandler("bekor", cancel)],
        allow_reentry=True,
    )

    # ── Handlerlarni ro'yxatga olish ──────────────────────
    app.add_handler(CommandHandler("start",   start))
    app.add_handler(CommandHandler("catalog", catalog))
    app.add_handler(CommandHandler("orders",  my_orders))
    app.add_handler(CommandHandler("admin",   admin_menu))
    app.add_handler(CommandHandler("referral",referral))
    app.add_handler(CommandHandler("balance", balance_cmd))
    app.add_handler(CommandHandler("savat",   lambda u,c: cart_view_cmd(u,c)))
    app.add_handler(CommandHandler("menu",    lambda u,c: show_main_menu(u,c,get_lang(u.effective_user.id))))

    # ── Pastki klaviatura text handler (eng yuqori, lekin ConvHandler dan keyin)
    menu_filter = filters.TEXT & ~filters.COMMAND & filters.Regex(
        "^(" + "|".join(k.replace("🛍","🛍").replace("(","\\(").replace(")","\\)") for k in ALL_MENU_TEXTS.keys()) + ")$"
    )
    app.add_handler(MessageHandler(menu_filter, menu_text_handler), group=0)

    # Conversation handlers (yuqori prioritet)
    app.add_handler(cart_conv)
    app.add_handler(edit_conv)
    app.add_handler(add_conv)
    app.add_handler(order_conv)
    app.add_handler(search_conv)
    app.add_handler(review_conv)
    app.add_handler(promo_conv)
    app.add_handler(broadcast_conv)
    app.add_handler(zone_conv)
    app.add_handler(stock_conv)
    app.add_handler(note_conv)

    # Callback handlers
    app.add_handler(CallbackQueryHandler(set_language,      pattern=r"^lang_"))
    app.add_handler(CallbackQueryHandler(menu_callback,     pattern=r"^menu_"))
    app.add_handler(CallbackQueryHandler(show_category,     pattern=r"^cat_"))
    app.add_handler(CallbackQueryHandler(show_product_cb,   pattern=r"^prod_\d+$"))
    app.add_handler(CallbackQueryHandler(back_catalog,      pattern="^back_catalog$"))
    app.add_handler(CallbackQueryHandler(admin_callback,    pattern=r"^adm_"))
    app.add_handler(CallbackQueryHandler(delete_product_cb, pattern=r"^delp_\d+$"))
    app.add_handler(CallbackQueryHandler(cart_add,          pattern=r"^cart_add_\d+$"))
    app.add_handler(CallbackQueryHandler(cart_view,         pattern="^cart_view$"))
    app.add_handler(CallbackQueryHandler(cart_clear,        pattern="^cart_clear$"))
    # ── To'lov oqimi ──────────────────────────────────────
    app.add_handler(CallbackQueryHandler(order_approve,     pattern=r"^oapprove_\d+$"))
    app.add_handler(CallbackQueryHandler(order_reject,      pattern=r"^oreject_\d+$"))
    app.add_handler(CallbackQueryHandler(user_pay_method,   pattern=r"^upay_\d+_"))
    app.add_handler(CallbackQueryHandler(receipt_ok,        pattern=r"^ochekok_\d+$"))
    app.add_handler(CallbackQueryHandler(receipt_reject,    pattern=r"^ochekrad_\d+$"))
    # ── Chek surat handler (konversatsiyadan tashqari) ────
    app.add_handler(MessageHandler(filters.PHOTO, receipt_photo_handler))
    app.add_handler(CallbackQueryHandler(noop,              pattern="^noop$"))

    # ── Rejalashtirilgan ishlar ────────────────────────────
    try:
        from datetime import time as dt_time
        jq = app.job_queue
        if jq is not None:
            jq.run_repeating(check_stuck_orders_job, interval=1800, first=60)
            jq.run_daily(daily_report_job, time=dt_time(hour=4, minute=0))
            print("✅ Job Queue faollashtirildi")
        else:
            print("⚠️  Job Queue mavjud emas (APScheduler o'rnatilmagan)")
    except Exception as e:
        print(f"⚠️  Job Queue xatosi: {e}")

    print("✅ PRO Shop Bot v2.0 ishga tushdi!")
    app.run_polling()


if __name__ == "__main__":
    main()
