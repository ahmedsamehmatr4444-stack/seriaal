import logging
import re
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = '8545045230:AAFxaE3jbwWVuiAbMLf-7Pd31nrjXd_4-zk'
CHANNEL_USERNAME = '@Serianumber99' 
LIST_MESSAGE_ID = 208

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ البوت يعمل بنجاح!\n⚠️ أرسل السكرين واكتب في الوصف:\n@Username | SerialNumber")

async def handle_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # الشرط الأول: التأكد من إرسال صورة
    if not update.message.photo:
        await update.message.reply_text("⚠️ خطأ! يجب إرسال سكرين شوت (صورة) لإتمام التسجيل.")
        return

    user_input = update.message.caption
    if not user_input:
        await update.message.reply_text("⚠️ يجب كتابة (اليوزر | السيريال) في وصف الصورة.")
        return

    # الشرط الثاني: التأكد من التنسيق (يوزر وسيريال فقط) ومنع أي كلام إضافي
    # النمط: @يوزر ثم فاصل ثم السيريال
    valid_format = re.match(r"^@[\w\d_]+\s*[|/-]\s*[\w\d_/]+$", user_input.strip())
    if not valid_format:
        await update.message.reply_text("❌ تنسيق الوصف غير صحيح! اكتبه كالتالي فقط:\n@Username | 12345678")
        return

    try:
        # إشعار للمستخدم
        status_msg = await update.message.reply_text("⏳ جاري تسجيل بياناتك في القناة...")

        # جلب القائمة من القناة
        temp_msg = await context.bot.forward_message(
            chat_id=update.effective_chat.id,
            from_chat_id=CHANNEL_USERNAME,
            message_id=LIST_MESSAGE_ID
        )
        current_text = temp_msg.text
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=temp_msg.message_id)

        # البحث عن خانة فارغة [ ]
        pattern = r"(\d+-\s*\[)\s*(\s*\])" 
        match = re.search(pattern, current_text)
        
        if not match:
            await status_msg.edit_text("❌ عذراً، القائمة ممتلئة بالكامل.")
            return

        current_num = match.group(1)
        new_entry = f"{current_num} {user_input} ]"
        updated_text = current_text.replace(match.group(0), new_entry, 1)

        # تعديل الرسالة في القناة
        await context.bot.edit_message_text(
            chat_id=CHANNEL_USERNAME,
            message_id=LIST_MESSAGE_ID,
            text=updated_text
        )

        await status_msg.edit_text(f"✅ تم بنجاح! تم تسجيلك في الخانة {current_num.replace('-', '').replace('[', '').strip()}")

    except Exception as e:
        await update.message.reply_text(f"❌ خطأ تقني: {str(e)}")

def main():
    application = ApplicationBuilder().token(TOKEN).build()
    
    # المعالجات
    application.add_handler(CommandHandler("start", start))
    # هيرد على الصور فقط، ولو حد بعت نص لوحده هيتجاهله أو ممكن نخليه ينبهه
    application.add_handler(MessageHandler(filters.PHOTO, handle_registration))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), 
        lambda u, c: u.message.reply_text("⚠️ لازم تبعت السكرين شوت وتكتب البيانات في الوصف!")))

    print("🚀 البوت يعمل الآن بالنسخة المستقرة...")
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
