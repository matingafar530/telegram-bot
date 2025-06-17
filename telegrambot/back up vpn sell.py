from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters
import random
import string
from datetime import datetime

BOT_TOKEN = '8137561831:AAGVf9uTt9ZLDYt-Gy-O7UF6g7JXDTafJQg'
ADMIN_CHAT_ID = 416940257  # آیدی عددی شما

# --- دیتابیس ساده ---
orders_db = {}
user_messages = {}

# --- منوها ---
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("1️⃣ خرید VPN", callback_data='buy')],
        [InlineKeyboardButton("2️⃣ پیگیری خرید", callback_data='track')],
        [InlineKeyboardButton("3️⃣ نرم‌افزارهای مورد نیاز", callback_data='apps')],
        [InlineKeyboardButton("📩 پیام به ادمین", callback_data='contact_admin')],
    ])

def vpn_plans_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("1️⃣ 1 ماهه / 1 کاربره (حجم نامحدود)", callback_data='plan_1m_1u')],
        [InlineKeyboardButton("2️⃣ 1 ماهه / 2 کاربره (حجم نامحدود)", callback_data='plan_1m_2u')],
        [InlineKeyboardButton("3️⃣ 3 ماهه / 1 کاربره (حجم نامحدود)", callback_data='plan_3m_1u')],
        [InlineKeyboardButton("4️⃣ 3 ماهه / 2 کاربره (حجم نامحدود)", callback_data='plan_3m_2u')],
        [InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_main')],
    ])

def payment_options_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 کارت به کارت", callback_data='pay_card')],
        [InlineKeyboardButton("💰 ارز دیجیتال", callback_data='pay_crypto')],
        [InlineKeyboardButton("🔙 بازگشت", callback_data='buy')],
    ])

def confirmation_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ تایید پرداخت", callback_data='confirm_payment')],
        [InlineKeyboardButton("❌ انصراف", callback_data='cancel_payment')],
    ])

def back_to_home_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 بازگشت به خانه", callback_data='back_to_main')],
    ])

def admin_decision_menu(order_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ تایید سفارش", callback_data=f'admin_approve_{order_id}')],
        [InlineKeyboardButton("❌ رد سفارش", callback_data=f'admin_reject_{order_id}')],
    ])

def apps_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("OpenConnect", callback_data='app_openconnect')],
        [InlineKeyboardButton("Cisco AnyConnect", callback_data='app_cisco')],
        [InlineKeyboardButton("V2Ray", callback_data='app_v2ray')],
        [InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_main')],
    ])

def os_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📱 اندروید", callback_data='os_android')],
        [InlineKeyboardButton("🍎 iOS", callback_data='os_ios')],
        [InlineKeyboardButton("💻 ویندوز", callback_data='os_windows')],
        [InlineKeyboardButton("🖥️ مک", callback_data='os_mac')],
        [InlineKeyboardButton("🐧 لینوکس", callback_data='os_linux')],
        [InlineKeyboardButton("🔙 بازگشت", callback_data='apps')],
    ])

# --- قیمت‌ها ---
PLAN_PRICES = {
    'plan_1m_1u': '150,000 تومان',
    'plan_1m_2u': '220,000 تومان',
    'plan_3m_1u': '300,000 تومان',
    'plan_3m_2u': '430,000 تومان',
}

# --- توابع کمکی ---
def generate_tracking_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def generate_order_id():
    return datetime.now().strftime("%Y%m%d%H%M%S") + ''.join(random.choices(string.digits, k=3))

async def send_to_admin(context, user_id, order_id):
    try:
        order = orders_db[order_id]
        admin_message = (
            f"📌 سفارش جدید! (#{order_id})\n"
            f"👤 کاربر: @{order['username'] or 'بدون نام کاربری'}\n"
            f"🆔 آیدی: {user_id}\n"
            f"📋 طرح: {order['plan']}\n"
            f"💰 قیمت: {order['price']}\n"
            f"💳 روش پرداخت: {order['payment_method']}\n"
            f"🔢 کد پیگیری: {order['tracking_code']}\n"
            f"🕒 زمان: {order['timestamp']}"
        )
        
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=admin_message,
            reply_markup=admin_decision_menu(order_id)
        )
        
        if 'receipt_photo_id' in order:
            await context.bot.forward_message(
                chat_id=ADMIN_CHAT_ID,
                from_chat_id=user_id,
                message_id=order['receipt_photo_id']
            )
        return True
    except Exception as e:
        print(f"خطا در ارسال به ادمین: {e}")
        return False

async def update_order_status(order_id, status, **kwargs):
    if order_id in orders_db:
        orders_db[order_id]['status'] = status
        for key, value in kwargs.items():
            orders_db[order_id][key] = value
        return True
    return False

# --- هندلرهای اصلی ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! 👋\nبه ربات فروش VPN خوش اومدی.\n\n🌐 خدمات ما:\n✅ خرید VPN مطمئن\n📦 پیگیری سفارش\n💡 نرم‌افزارهای اتصال",
        reply_markup=main_menu()
    )

async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    # --- منوی اصلی ---
    if data == 'back_to_main':
        await query.edit_message_text(
            "سلام! 👋\nبه ربات فروش VPN خوش اومدی.\n\n🌐 خدمات ما:\n✅ خرید VPN مطمئن\n📦 پیگیری سفارش\n💡 نرم‌افزارهای اتصال",
            reply_markup=main_menu()
        )
    
    # --- خرید VPN ---
    elif data == 'buy':
        await query.edit_message_text("💳 لطفاً یکی از طرح‌های زیر را انتخاب کنید:", reply_markup=vpn_plans_menu())

    elif data in PLAN_PRICES:
        price = PLAN_PRICES[data]
        context.user_data['current_order'] = {
            'plan': data,
            'price': price,
            'username': query.from_user.username
        }
        await query.edit_message_text(
            f"💰 قیمت این طرح: {price}\n\n📌 لطفاً روش پرداخت خود را انتخاب کنید:",
            reply_markup=payment_options_menu()
        )

    elif data == 'pay_card':
        context.user_data['current_order']['payment_method'] = 'کارت به کارت'
        await query.edit_message_text(
            "💳 شماره کارت جهت واریز:\n```6037 9975 4052 9022```\n\n"
            "لطفاً بعد از پرداخت، اسکرین‌شات تاییدیه انتقال مبلغ را ارسال کنید و سپس دکمه تایید را بزنید.",
            reply_markup=confirmation_menu()
        )

    elif data == 'pay_crypto':
        context.user_data['current_order']['payment_method'] = 'ارز دیجیتال'
        await query.edit_message_text(
            "💰 آدرس کیف پول ارز دیجیتال:\n```\nUSDT (TRC20): TMgH1YtU2X56C...\n```\n\n"
            "لطفاً بعد از پرداخت، اسکرین‌شات تاییدیه انتقال مبلغ را ارسال کنید و سپس دکمه تایید را بزنید.",
            reply_markup=confirmation_menu()
        )

    elif data == 'confirm_payment':
        if 'receipt_sent' in context.user_data.get('current_order', {}):
            order_id = generate_order_id()
            tracking_code = generate_tracking_code()
            
            orders_db[order_id] = {
                **context.user_data['current_order'],
                'tracking_code': tracking_code,
                'status': 'در حال بررسی',
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'user_id': query.from_user.id
            }
            
            if 'receipt_photo_id' in context.user_data['current_order']:
                orders_db[order_id]['receipt_photo_id'] = context.user_data['current_order']['receipt_photo_id']
            
            # ارسال پیام دائمی به کاربر
            await context.bot.send_message(
                chat_id=query.from_user.id,
                text=f"✅ سفارش شما ثبت شد!\n\n🔢 کد پیگیری: <code>{tracking_code}</code>\n🕒 زمان ثبت: {orders_db[order_id]['timestamp']}\n\nوضعیت: در حال بررسی\n\nمی‌توانید با ارسال کد پیگیری وضعیت سفارش را پیگیری کنید.",
                parse_mode='HTML'
            )
            
            # ارسال به ادمین
            await send_to_admin(context, query.from_user.id, order_id)
            
            await query.edit_message_text(
                "✅ سفارش شما با موفقیت ثبت شد. کد پیگیری به شما ارسال شد.\n\nمی‌توانید از منوی اصلی وضعیت سفارش را پیگیری کنید.",
                reply_markup=back_to_home_menu()
            )
            
            # پاک کردن داده‌های موقت
            del context.user_data['current_order']
        else:
            await query.edit_message_text(
                "⚠️ شما هنوز عکسی مبنی بر تاییدیه انتقال مبلغ ارسال نکرده‌اید.\n\n"
                "لطفاً اسکرین‌شات تاییدیه را ارسال کنید و سپس دکمه تایید را بزنید.",
                reply_markup=confirmation_menu()
            )

    elif data == 'cancel_payment':
        await query.edit_message_text(
            "💳 لطفاً یکی از طرح‌های زیر را انتخاب کنید:",
            reply_markup=vpn_plans_menu()
        )

    # --- پیگیری سفارش ---
    elif data == 'track':
        await query.edit_message_text("🕵️ لطفاً شماره سفارش (کد پیگیری) خود را ارسال کنید:")

    # --- نرم‌افزارها ---
    elif data == 'apps':
        await query.edit_message_text("📥 نرم‌افزار مورد نیاز را انتخاب کنید:", reply_markup=apps_menu())

    elif data in ['app_openconnect', 'app_cisco', 'app_v2ray']:
        app_name = {
            'app_openconnect': "OpenConnect",
            'app_cisco': "Cisco AnyConnect",
            'app_v2ray': "V2Ray"
        }[data]
        await query.edit_message_text(f"📲 سیستم‌عامل مورد نظر برای {app_name} را انتخاب کنید:", reply_markup=os_menu())

    elif data.startswith('os_'):
        os_name = {
            'os_android': "اندروید",
            'os_ios': "iOS",
            'os_windows': "ویندوز",
            'os_mac': "مک",
            'os_linux': "لینوکس"
        }[data]
        await query.edit_message_text(f"🔗 لینک یا فایل مربوط به {os_name} در حال آماده‌سازی است...")

    # --- پیام به ادمین ---
    elif data == 'contact_admin':
        await query.edit_message_text("📩 لطفاً پیام خود را برای ادمین ارسال کنید:")

    # --- مدیریت ادمین ---
    elif data.startswith('admin_approve_'):
        order_id = data.split('_')[-1]
        user_messages[query.from_user.id] = {
            'type': 'get_vpn_credentials',
            'order_id': order_id
        }
        await query.edit_message_text(f"لطفاً نام کاربری و رمز عبور VPN را برای سفارش #{order_id} ارسال کنید:")

    elif data.startswith('admin_reject_'):
        order_id = data.split('_')[-1]
        user_messages[query.from_user.id] = {
            'type': 'get_rejection_reason',
            'order_id': order_id
        }
        await query.edit_message_text(f"لطفاً دلیل رد سفارش #{order_id} را ارسال کنید:")

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text
    
    # --- پردازش پیام‌های متنی ---
    if text:
        # پیگیری سفارش
        if 'current_order' not in context.user_data and any(order['tracking_code'] == text for order in orders_db.values() if order.get('user_id') == user_id):
            order = next(order for order in orders_db.values() if order.get('tracking_code') == text and order.get('user_id') == user_id)
            status_messages = {
                'در حال بررسی': "🔍 سفارش شما در حال بررسی است. لطفاً شکیبا باشید.",
                'تایید شده': f"✅ سفارش شما تایید شده است!\n\n🔑 اطلاعات اتصال:\n👤 نام کاربری: {order.get('vpn_username', 'N/A')}\n🔒 رمز عبور: {order.get('vpn_password', 'N/A')}",
                'رد شده': f"❌ سفارش شما رد شده است.\n\nدلیل: {order.get('rejection_reason', 'عدم مشخص')}"
            }
            
            await update.message.reply_text(
                f"🔍 وضعیت سفارش:\n\n"
                f"🔢 کد پیگیری: {order['tracking_code']}\n"
                f"📋 طرح: {order['plan']}\n"
                f"💰 قیمت: {order['price']}\n"
                f"🕒 زمان ثبت: {order['timestamp']}\n\n"
                f"وضعیت: {status_messages.get(order['status'], order['status'])}",
                reply_markup=back_to_home_menu()
            )
        
        # پیام به ادمین
        elif 'contact_admin' in context.user_data:
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=f"📩 پیام از کاربر:\n👤 آیدی: {user_id}\n📝 متن:\n{text}"
            )
            await update.message.reply_text(
                "✅ پیام شما به ادمین ارسال شد.",
                reply_markup=back_to_home_menu()
            )
            del context.user_data['contact_admin']
        
        # پردازش پاسخ‌های ادمین
        elif user_id == ADMIN_CHAT_ID and user_id in user_messages:
            msg_type = user_messages[user_id]['type']
            order_id = user_messages[user_id]['order_id']
            
            if msg_type == 'get_vpn_credentials':
                await update_order_status(
                    order_id,
                    'تایید شده',
                    vpn_username=text.split()[0] if ' ' in text else text,
                    vpn_password=text.split()[1] if ' ' in text else 'رمز یکسان'
                )
                order = orders_db[order_id]
                await context.bot.send_message(
                    chat_id=order['user_id'],
                    text=f"✅ سفارش شما تایید شد!\n\n🔢 کد پیگیری: {order['tracking_code']}\n\n🔑 اطلاعات اتصال:\n👤 نام کاربری: {order['vpn_username']}\n🔒 رمز عبور: {order['vpn_password']}",
                    reply_markup=back_to_home_menu()
                )
                await update.message.reply_text("✅ اطلاعات VPN برای کاربر ارسال شد.")
            
            elif msg_type == 'get_rejection_reason':
                await update_order_status(
                    order_id,
                    'رد شده',
                    rejection_reason=text
                )
                order = orders_db[order_id]
                await context.bot.send_message(
                    chat_id=order['user_id'],
                    text=f"❌ متأسفیم! سفارش شما رد شد.\n\n🔢 کد پیگیری: {order['tracking_code']}\n\nدلیل: {order['rejection_reason']}",
                    reply_markup=back_to_home_menu()
                )
                await update.message.reply_text("✅ دلیل رد سفارش برای کاربر ارسال شد.")
            
            del user_messages[user_id]

async def handle_receipt_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'current_order' in context.user_data:
        context.user_data['current_order']['receipt_sent'] = True
        context.user_data['current_order']['receipt_photo_id'] = update.message.message_id
        await update.message.reply_text(
            "✅ عکس تاییدیه دریافت شد. لطفاً دکمه تایید را بزنید.",
            reply_markup=confirmation_menu()
        )

# --- اجرای ربات ---
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # هندلرهای اصلی
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callbacks))
    
    # هندلرهای پیام‌ها
    app.add_handler(MessageHandler(filters.PHOTO, handle_receipt_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))
    
    print("🤖Starting engine...")
    app.run_polling()

if __name__ == '__main__':
    main()