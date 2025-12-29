import logging
import requests
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters


TOKEN = "8414599674:AAFn_mNJIKUBCb6WWGuKLB9XXh3qBNkeyk4"
MOPON_URL = 'https://www.mopon.ir/api/coupon/single/xVMOq'

HEADERS = {
    'authority': 'www.mopon.ir',
    'accept': '*/*',
    'accept-language': 'en-GB,en;q=0.9,fa-IR;q=0.8,fa;q=0.7,en-US;q=0.6',
    'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
    'sec-ch-ua-mobile': '?1',
    'sec-ch-ua-platform': '"Android"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36',
    'x-requested-with': 'XMLHttpRequest',
}

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


def get_proxy_dict(proxy_str):
    
    if not proxy_str:
        return None
    return {
        "http": f"http://{proxy_str}",
        "https": f"http://{proxy_str}",
    }

def get_main_menu_keyboard():
    
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📥 تنظیم لینک پروکسی", callback_data='set_proxy_url'),
            InlineKeyboardButton("🌐 نمایش IP سرور", callback_data='show_ip'),
        ],
        [
            InlineKeyboardButton("🎫 استخراج کوپن", callback_data='extract_coupon'),
        ]
    ])

def get_back_button():
    
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🏠 بازگشت به منو", callback_data='back_to_menu')
    ]])



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    context.user_data['state'] = None
    
    await update.message.reply_text(
        "👋 سلام! به ربات استخراج کوپن خوش آمدید.\nلطفا یک گزینه را انتخاب کنید:", 
        reply_markup=get_main_menu_keyboard()
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    query = update.callback_query
    await query.answer()
    
    
    if query.data == 'back_to_menu':
        context.user_data['state'] = None
        await query.edit_message_text(
            text="👋 به ربات استخراج کوپن خوش آمدید.\nلطفا یک گزینه را انتخاب کنید:",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    
    if query.data == 'show_ip':
        try:
            ip = requests.get('https://api.ipify.org', timeout=5).text
            await query.edit_message_text(
                text=f"🌐 IP سرور ربات: `{ip}`",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_back_button()
            )
        except Exception as e:
            await query.edit_message_text(
                text=f"❌ خطا در دریافت IP: {e}",
                reply_markup=get_back_button()
            )
        return
            
    
    if query.data == 'set_proxy_url':
        context.user_data['state'] = 'WAITING_PROXY_URL'
        await query.edit_message_text(
            text="🔗 لطفاً لینک فایل TXT پروکسی را ارسال کنید:\n(مثال: https://site.com/proxy.txt)\n\nبرای لغو /start را بزنید.",
            reply_markup=get_back_button()
        )
        return
        
    
    if query.data == 'extract_coupon':
        context.user_data['state'] = 'WAITING_COUNT'
        proxies = context.user_data.get('proxies', [])
        proxy_msg = f"✅ {len(proxies)} پروکسی فعال است." if proxies else "⚠️ پروکسی تنظیم نشده (اتصال مستقیم)."
        await query.edit_message_text(
            text=f"{proxy_msg}\n\n🔢 تعداد درخواست‌ها را به عدد وارد کنید (مثلا 10):\n\nبرای لغو /start را بزنید.",
            reply_markup=get_back_button()
        )
        return

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت پیام‌های متنی کاربر"""
    state = context.user_data.get('state')
    
    
    if state == 'WAITING_PROXY_URL':
        url = update.message.text.strip()
        msg = await update.message.reply_text("⏳ در حال دانلود و بررسی لیست پروکسی...")
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                proxies = [line.strip() for line in response.text.splitlines() if line.strip()]
                context.user_data['proxies'] = proxies
                context.user_data['state'] = None
                
                await msg.edit_text(
                    f"✅ لیست پروکسی با موفقیت آپدیت شد.\nتعداد پروکسی‌ها: {len(proxies)}",
                    reply_markup=get_back_button()
                )
            else:
                await msg.edit_text(
                    f"❌ خطا در دانلود فایل. کد وضعیت: {response.status_code}",
                    reply_markup=get_back_button()
                )
        except Exception as e:
            await msg.edit_text(
                f"❌ خطا: {str(e)}",
                reply_markup=get_back_button()
            )

    
    elif state == 'WAITING_COUNT':
        try:
            count = int(update.message.text)
            if count > 50:
                await update.message.reply_text(
                    "⚠️ تعداد زیاد است. لطفا عددی کمتر از 50 وارد کنید.",
                    reply_markup=get_back_button()
                )
                return
            
            if count < 1:
                await update.message.reply_text(
                    "⚠️ تعداد باید حداقل 1 باشد.",
                    reply_markup=get_back_button()
                )
                return
                
            msg = await update.message.reply_text(f"🚀 شروع استخراج {count} کوپن...\nلطفا صبر کنید.")
            
            proxies_list = context.user_data.get('proxies', [])
            results = []
            
            
            for i in range(count):
                proxy_dict = None
                if proxies_list:
                    current_proxy = random.choice(proxies_list)
                    proxy_dict = get_proxy_dict(current_proxy)
                
                try:
                    response = requests.get(MOPON_URL, headers=HEADERS, proxies=proxy_dict, timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        if 'data' in data and 'code' in data['data']:
                            coupon = data['data']['code'].strip()
                            results.append(coupon)
                except:
                    pass
                
                
                if (i + 1) % 10 == 0:
                    try:
                        await msg.edit_text(f"⏳ در حال پردازش... ({i + 1}/{count})")
                    except:
                        pass
            
            
            if results:
                output_text = "🎫 لیست کوپن‌های دریافت شده:\n\n"
                for idx, code in enumerate(results, 1):
                    output_text += f"{idx}. `{code}`\n"
                
                
                if len(output_text) > 4000:
                    
                    chunks = [output_text[i:i+4000] for i in range(0, len(output_text), 4000)]
                    await msg.edit_text(chunks[0], parse_mode=ParseMode.MARKDOWN)
                    for chunk in chunks[1:]:
                        await update.message.reply_text(chunk, parse_mode=ParseMode.MARKDOWN)
                    await update.message.reply_text(
                        f"✅ استخراج تکمیل شد. تعداد کل: {len(results)}",
                        reply_markup=get_back_button()
                    )
                else:
                    await msg.edit_text(output_text, parse_mode=ParseMode.MARKDOWN)
                    await update.message.reply_text(
                        f"✅ استخراج تکمیل شد!",
                        reply_markup=get_back_button()
                    )
            else:
                await msg.edit_text(
                    "😔 هیچ کوپنی دریافت نشد. ممکن است پروکسی‌ها مشکل داشته باشند یا API تغییر کرده باشد.",
                    reply_markup=get_back_button()
                )
            
            context.user_data['state'] = None
            
        except ValueError:
            await update.message.reply_text(
                "❌ لطفا فقط عدد وارد کنید.",
                reply_markup=get_back_button()
            )


if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    print("🤖 Robot is running...")
    app.run_polling()
