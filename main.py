import logging
import re
import asyncio
import io
import numpy as np
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler

# مكتبات معالجة الصور وقراءتها
try:
    from PIL import Image
    import easyocr
    # تجهيز القارئ (يدعم الإنجليزية)
    reader = easyocr.Reader(['en'])
except ImportError:
    print("تأكد من إضافة easyocr و Pillow و opencv-python-headless في ملف requirements.txt")

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = '8545045230:AAFxaE3jbwWVuiAbMLf-7Pd31nrjXd_4-zk'
CHANNEL_USERNAME = '@Serianumber99' 
LIST_MESSAGE_ID = 208

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ البوت يعمل! أرسل السكرين واكتب البيانات في الوصف.\n⚠️ شرط التسجيل: وجود كلمة Serial number داخل الصورة والوصف (يوزر | سيريال) فقط.")

async def handle_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        return

    user_input = update.message.caption
    if not user_input:
        await update.message.reply_text("⚠️ اكتب (اليوزر | السيريال) في وصف الصورة.")
        return

    # 1. التأكد من أن الوصف يحتوي على اليوزر والسيريال فقط (بدون كلام إضافي)
    # النمط: يوزر يبدأ بـ @ ثم فاصل ثم السيريال
    valid_format = re.match(r"^@[\w\d_]+\s*[|/-]\s*[\w\d_/]+$", user_input.strip())
    if not valid_format:
        await update.message.reply_text("❌ خطأ! يجب أن يحتوي الوصف على اليوزر والسيريال فقط بهذا التنسيق:\n@Username | SerialNumber")
        return

    try:
        # 2. فحص الصورة لقراءة كلمة Serial number
        status_msg = await update.message.reply_text("🔍 جاري فحص الصورة، انتظر لحظة...")
        
        photo_file = await update.message.photo[-1].get_file()
        photo_bytes = await photo_file.download_as_bytearray()
        
        # تحويل الصورة لصيغة يفهمها EasyOCR
        image = Image.open(io.BytesIO(photo_bytes))
        image_np = np.array(image)
        
        # قراءة النص من الصورة
        results = reader.readtext(image_np, detail=0)
        extracted_text = " ".join(results).lower()

        # التأكد من وجود الكلمة المطلوبة
        if "serial" not in extracted_text and "number" not in extracted_text:
            await status_msg.edit_text("❌ الصورة مرفوضة! لم يتم العثور على حقل (Serial number) داخل السكرين.")
            return

        await status_msg.delete()

        # 3. تكملة الكود الأصلي للتعديل على القناة
        temp_msg = await context.bot.forward_message(
            chat_id=update.effective_chat.id,
            from_chat_id=CHANNEL_USERNAME,
            message_id=LIST_MESSAGE_ID
        )
        current_text = temp_msg.text
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=temp_msg.message_id)

        pattern = r"(\d+-\s*\[)\s*(\s*\])" 
        match = re.search(pattern, current_text)
        
        if not match:
            await update.message.reply_text("❌ القائمة ممتلئة!")
            return

        current_num = match.group(1)
        new_entry = f"{current_num} {user_input} ]"
        updated_text = current_text.replace(match.group(0), new_entry, 1)

        await context.bot.edit_message_text(
            chat_id=CHANNEL_USERNAME,
            message_id=LIST_MESSAGE_ID,
            text=updated_text
        )

        await update.message.reply_text(f"✅ تم تسجيلك بنجاح في الخانة {current_num.replace('-', '').strip()}")

    except Exception as e:
        await update.message.reply_text(f"❌ حدث خطأ: {str(e)}")

def main():
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, handle_registration))
    print("🚀 البوت بدأ العمل بنظام فحص الصور الذكي...")
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
