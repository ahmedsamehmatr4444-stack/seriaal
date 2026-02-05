import logging
import re
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler, CallbackQueryHandler

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = '8545045230:AAFxaE3jbwWVuiAbMLf-7Pd31nrjXd_4-zk'
CHANNEL_USERNAME = '@Serianumber99' 
LIST_MESSAGE_ID = 208 # الرسالة التي تحتوي على القائمة الرئيسية [ ]
ADMIN_IDS = [8147516847, 6661924074]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 بوت الفحص التاريخي يعمل!\nسأقوم بفحص القناة من الرسالة رقم 1 حتى 208 للتأكد من بياناتك.")

async def handle_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo: return
    user_input = update.message.caption
    if not user_input:
        await update.message.reply_text("⚠️ اكتب (اليوزر | السيريال) في وصف الصورة.")
        return

    match_input = re.match(r"^(@[\w\d_]+)\s*[|/-]\s*([\w\d_/]+)$", user_input.strip())
    if not match_input:
        await update.message.reply_text("❌ تنسيق خاطئ! استخدم: @Username | Serial")
        return

    new_user = match_input.group(1)
    new_serial = match_input.group(2)

    status_msg = await update.message.reply_text("🔍 جاري فحص أرشيف القناة بالكامل (1 ⬅️ 208)...")

    found_info = None
    # --- الفحص التاريخي من الرسالة 1 لـ 208 ---
    for msg_id in range(1, LIST_MESSAGE_ID + 1):
        try:
            # استخدام forward مؤقت لقراءة محتوى الرسائل القديمة
            old_msg = await context.bot.forward_message(chat_id=update.effective_chat.id, from_chat_id=CHANNEL_USERNAME, message_id=msg_id)
            content = old_msg.text if old_msg.text else (old_msg.caption if old_msg.caption else "")
            
            if new_serial.lower() in content.lower():
                found_info = f"السيريال موجود مسبقاً في الرسالة {msg_id}"
                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=old_msg.message_id)
                break
            elif new_user.lower() in content.lower():
                found_info = f"اليوزر موجود مسبقاً في الرسالة {msg_id}"
                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=old_msg.message_id)
                break
            
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=old_msg.message_id)
            # تأخير بسيط لتجنب حظر التليجرام (Flood Control)
            await asyncio.sleep(0.05)
        except:
            continue

    await status_msg.delete()

    # إرسال التقرير للأدمن
    report = found_info if found_info else "✅ بيانات جديدة كلياً (إضافة لاعب)."
    
    for admin_id in ADMIN_IDS:
        keyboard = [[
            InlineKeyboardButton("✅ تنفيذ العملية", callback_data=f"exec_{update.message.chat_id}"),
            InlineKeyboardButton("❌ رفض", callback_data=f"reject_{update.message.chat_id}")
        ]]
        context.bot_data[f"u_{update.message.chat_id}"] = new_user
        context.bot_data[f"s_{update.message.chat_id}"] = new_serial
        
        await context.bot.send_photo(
            chat_id=admin_id,
            photo=update.message.photo[-1].file_id,
            caption=f"📝 **تقرير الفحص:**\n{report}\n\n👤 المطلوب: {new_user}\n🔢 السيريال: {new_serial}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    await update.message.reply_text("⏳ انتهى الفحص الشامل وتم إرسال التقرير للإدارة.")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action, user_chat_id = query.data.split("_")
    
    if action == "exec":
        new_user = context.bot_data.get(f"u_{user_chat_id}")
        new_serial = context.bot_data.get(f"s_{user_chat_id}")
        
        try:
            # تعديل القائمة في الرسالة 208
            temp_msg = await context.bot.forward_message(chat_id=query.message.chat_id, from_chat_id=CHANNEL_USERNAME, message_id=LIST_MESSAGE_ID)
            lines = temp_msg.text.split('\n')
            await context.bot.delete_message(chat_id=query.message.chat_id, message_id=temp_msg.message_id)

            updated = False
            # البحث في سطور القائمة (208) لتعديل السطر المطابق أو إيجاد خانة فاضية
            for i, line in enumerate(lines):
                if new_serial.lower() in line.lower() or new_user.lower() in line.lower() or "[ ]" in line:
                    prefix = re.match(r"(\d+-\s*\[)", line)
                    if prefix:
                        lines[i] = f"{prefix.group(1)} {new_user} | {new_serial} ]"
                        updated = True
                        break
            
            if updated:
                await context.bot.edit_message_text(chat_id=CHANNEL_USERNAME, message_id=LIST_MESSAGE_ID, text="\n".join(lines))
                await context.bot.send_message(chat_id=user_chat_id, text="✅ تمت الموافقة وتحديث بياناتك في القائمة.")
                await query.edit_message_caption(caption=f"{query.message.caption}\n\n✅ تم التنفيذ بنجاح.")
        except Exception as e:
            await query.edit_message_caption(caption=f"❌ خطأ: {e}")

    elif action == "reject":
        await context.bot.send_message(chat_id=user_chat_id, text="❌ تم رفض طلبك.")
        await query.edit_message_caption(caption=f"{query.message.caption}\n\n❌ مرفوض.")

def main():
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, handle_registration))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.run_polling()

if __name__ == '__main__':
    main()
