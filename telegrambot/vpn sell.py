from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters
import random
import string
from datetime import datetime

BOT_TOKEN = '8137561831:AAGVf9uTt9ZLDYt-Gy-O7UF6g7JXDTafJQg'
ADMIN_CHAT_ID = 416940257

orders_db = {}
user_messages = {}
admin_responses = {}
admin_flows = {}

# --- منوها ---
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("1️⃣ خرید VPN", callback_data='buy')],
        [InlineKeyboardButton("2️⃣ پیگیری خرید", callback_data='track')],
        [InlineKeyboardButton("3️⃣ نرم‌افزارهای مورد نیاز", callback_data='apps')],
        [InlineKeyboardButton("📩 پیام به ادمین", callback_data='contact_admin')],
        [InlineKeyboardButton("📘 آموزش اتصال به VPN", callback_data='guide')],
    ])

def payment_options_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 کارت به کارت", callback_data='pay_card')],
        [InlineKeyboardButton("💰 ارز دیجیتال", callback_data='pay_crypto')],
        [InlineKeyboardButton("🔙 بازگشت", callback_data='buy')],
    ])

def back_to_payment_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 بازگشت به انتخاب روش پرداخت", callback_data='buy')]
    ])

def back_to_home_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 بازگشت به خانه", callback_data='back_to_main')],
    ])

def guide_text():
    return """📘 آموزش اتصال به VPN:

(در اینجا بعداً متن کامل آموزش قرار داده خواهد شد)
""", back_to_home_menu()

# --- هندلرها ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! 👋\nبه ربات فروش VPN خوش اومدی.",
        reply_markup=main_menu()
    )

async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    if data == 'back_to_main':
        await query.edit_message_text("سلام! 👋\nبه ربات فروش VPN خوش اومدی.", reply_markup=main_menu())

    elif data == 'contact_admin':
        context.user_data['contact_admin'] = True
        await query.edit_message_text("📩 لطفاً پیام خود را برای ادمین ارسال کنید:")

    elif data == 'pay_crypto':
        await query.edit_message_text(
            "❗ بخش پرداخت با ارز دیجیتال فعلاً در دسترس نیست.",
            reply_markup=back_to_payment_menu()
        )

    elif data == 'guide':
        text, reply_markup = guide_text()
        await query.edit_message_text(text=text, reply_markup=reply_markup)

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text
    username = update.message.from_user.username or "بدون یوزرنیم"

    # پیام مشتری به ادمین
    if context.user_data.get('contact_admin'):
        msg = f"📩 پیام از مشتری\n👤 یوزرنیم: @{username}\n🆔 آیدی: {user_id}\n\n📝 پیام:\n{text}"
        sent = await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=msg)
        admin_responses[sent.message_id] = user_id
        await update.message.reply_text("✅ پیام شما به ادمین ارسال شد.", reply_markup=back_to_home_menu())
        del context.user_data['contact_admin']

    elif user_id == ADMIN_CHAT_ID and update.message.reply_to_message and update.message.reply_to_message.message_id in admin_responses:
        target_id = admin_responses[update.message.reply_to_message.message_id]
        await context.bot.send_message(chat_id=target_id, text=f"📩 پاسخ ادمین:\n{text}")
        await update.message.reply_text("✅ پاسخ شما برای مشتری ارسال شد.")
        del admin_responses[update.message.reply_to_message.message_id]

    elif user_id == ADMIN_CHAT_ID and user_id in admin_flows:
        step = admin_flows[user_id]['step']
        order_id = admin_flows[user_id]['order_id']

        if step == 'username':
            admin_flows[user_id]['vpn_username'] = text
            admin_flows[user_id]['step'] = 'password'
            await update.message.reply_text("🔒 لطفاً رمز عبور VPN را وارد کنید:")

        elif step == 'password':
            vpn_username = admin_flows[user_id]['vpn_username']
            vpn_password = text
            orders_db[order_id]['vpn_username'] = vpn_username
            orders_db[order_id]['vpn_password'] = vpn_password
            orders_db[order_id]['status'] = 'تایید شده'

            order = orders_db[order_id]
            await context.bot.send_message(
                chat_id=order['user_id'],
                text=f"✅ سفارش شما تایید شد!\n\n🔢 کد پیگیری: {order['tracking_code']}\n\n🔑 اطلاعات اتصال:\n👤 نام کاربری: {vpn_username}\n🔒 رمز عبور: {vpn_password}\n🌐 لینک اتصال: https://ger.raptor.website",
                reply_markup=back_to_home_menu()
            )
            await update.message.reply_text("✅ اطلاعات برای کاربر ارسال شد.")
            del admin_flows[user_id]

# --- اجرای ربات ---
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callbacks))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))
    print("🤖 Starting engine....")
    app.run_polling()

if __name__ == '__main__':
    main()
