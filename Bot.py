import logging
import requests
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters

TOKEN = "8414599674:AAFn_mNJIKUBCb6WWGuKLB9XXh3qBNkeyk4"
S_KEY = "7a3c7e2b53610912d6c4778afd570667"
MOPON_URL = 'https://www.mopon.ir/api/coupon/single/xVMOq'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def get_main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📥 تنظیم لینک پروکسی", callback_data='set_proxy_url'),
         InlineKeyboardButton("🌐 نمایش IP سرور", callback_data='show_ip')],
        [InlineKeyboardButton("🎫 استخراج کوپن", callback_data='extract_coupon')]
    ])

def get_back_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🏠 بازگشت به منو", callback_data='back_to_menu')]])

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
            payload = {'api_key': S_KEY, 'url': 'https://api.ipify.org'}
            r = requests.get('http://api.scraperapi.com', params=payload)
            ip = r.text
            await query.edit_message_text(
                text=f"🌐 IP متصل شده (پروکسی): `{ip}`",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_back_button()
            )
        except Exception as e:
            await query.edit_message_text(f"❌ خطا در دریافت IP: {e}", reply_markup=get_back_button())
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
        proxy_msg = f"✅ {len(proxies)} پروکسی فعال آماده استفاده است." if proxies else "⚠️ پروکسی ست نشده (استفاده از پروکسی پیش‌فرض سیستم)."
        await query.edit_message_text(
            text=f"{proxy_msg}\n\n🔢 تعداد درخواست‌ها را به عدد وارد کنید:",
            reply_markup=get_back_button()
        )
        return

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
                    f"✅ لیست پروکسی با موفقیت آپدیت شد.\nتعداد پروکسی‌های سالم: {len(proxies)}",
                    reply_markup=get_back_button()
                )
            else:
                await msg.edit_text("❌ خطا در دانلود فایل.", reply_markup=get_back_button())
        except Exception as e:
            await msg.edit_text(f"❌ خطا: {str(e)}", reply_markup=get_back_button())

    elif state == 'WAITING_COUNT':
        try:
            count = int(update.message.text)
            if count > 50:
                await update.message.reply_text("⚠️ تعداد زیاد است (حداکثر ۵۰).", reply_markup=get_back_button())
                return
            
            msg = await update.message.reply_text(f"🚀 شروع چرخش بین پروکسی‌ها و استخراج {count} کوپن...")
            results = []
            
            for i in range(count):
                try:
                    payload = {'api_key': S_KEY, 'url': MOPON_URL}
                    response = requests.get('http://api.scraperapi.com', params=payload, timeout=20)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if 'data' in data and 'code' in data['data']:
                            results.append(data['data']['code'].strip())
                    
                    if (i + 1) % 5 == 0:
                        await msg.edit_text(f"⏳ در حال تغییر IP و پردازش... ({i + 1}/{count})")
                except:
                    pass

            if results:
                output_text = "🎫 لیست کوپن‌های دریافت شده:\n\n"
                for idx, code in enumerate(results, 1):
                    output_text += f"{idx}. `{code}`\n"
                
                if len(output_text) > 4000:
                    await msg.edit_text(output_text[:4000], parse_mode=ParseMode.MARKDOWN)
                    await update.message.reply_text(output_text[4000:], parse_mode=ParseMode.MARKDOWN)
                else:
                    await msg.edit_text(output_text, parse_mode=ParseMode.MARKDOWN)
                
                await update.message.reply_text(f"✅ عملیات با موفقیت انجام شد.", reply_markup=get_back_button())
            else:
                await msg.edit_text("😔 هیچ کوپنی یافت نشد. پروکسی‌ها را تغییر دهید.", reply_markup=get_back_button())
            
            context.user_data['state'] = None
        except ValueError:
            await update.message.reply_text("❌ فقط عدد وارد کنید.", reply_markup=get_back_button())

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    print("Running...")
    app.run_polling()
