import logging
import re
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler, CallbackQueryHandler

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = '8545045230:AAFxaE3jbwWVuiAbMLf-7Pd31nrjXd_4-zk'
CHANNEL_USERNAME = '@Serianumber99' 
LIST_MESSAGE_ID = 208 # الرسالة التي تحتوي على القائمة الرئيسية
GROUP_ID = -1002588398038 # الكروب الذي ستتم فيه الموافقة والرفض

# قائمة المشرفين المسموح لهم بالتحكم الكامل
ADMIN_USERNAMES = [
    "ahsvsjsv", "OQO_e1", "H4_OT", "Q_12_T", "h896556", 
    "murtaza_said", "c1c_2", "BOTrika_22", "oaa_c", "mwsa_20", 
    "feloo9", "yas_r7", "Hu2009", "PHT_10", "l_7yk", "levil_8"
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 بوت الفحص الذكي يعمل بنجاح!")

async def handle_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo: return
    user_input = update.message.caption
    if not user_input: return

    # تحسين التعرف على المدخلات (يوزر | سيريال)
    match_input = re.match(r"^(@[\w\d_]+)\s*[|/-]\s*([\w\d_/]+)$", user_input.strip())
    if not match_input: return

    new_user = match_input.group(1)
    new_serial = match_input.group(2)

    status_msg = await update.message.reply_text("🔍 جاري فحص الأرشيف...")

    found_info = "✅ بيانات جديدة."
    is_update = False
    
    # فحص الأرشيف
    for msg_id in range(1, LIST_MESSAGE_ID + 1):
        try:
            old_msg = await context.bot.forward_message(chat_id=update.effective_chat.id, from_chat_id=CHANNEL_USERNAME, message_id=msg_id)
            content = (old_msg.text or old_msg.caption or "").lower()
            if new_serial.lower() in content or new_user.lower() in content:
                found_info = f"⚠️ بيانات موجودة مسبقاً في الرسالة {msg_id}"
                is_update = True
                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=old_msg.message_id)
                break
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=old_msg.message_id)
            await asyncio.sleep(0.02)
        except: continue

    await status_msg.delete()
    
    # إخبار المستخدم بأن طلبه أرسل للإدارة بعد الفحص
    await update.message.reply_text("✅ تم فحص الأرشيف بنجاح، وتم إرسال طلبك للإدارة للموافقة.")

    keyboard = [[
        InlineKeyboardButton("✅ قبول التنفيذ", callback_data=f"exec_{update.message.chat_id}"),
        InlineKeyboardButton("❌ رفض", callback_data=f"reject_{update.message.chat_id}")
    ]]
    
    context.bot_data[f"u_{update.message.chat_id}"] = new_user
    context.bot_data[f"s_{update.message.chat_id}"] = new_serial
    context.bot_data[f"is_update_{update.message.chat_id}"] = is_update
    
    await context.bot.send_photo(
        chat_id=GROUP_ID,
        photo=update.message.photo[-1].file_id,
        caption=f"📝 **تقرير فحص:**\n{found_info}\n👤 اليوزر: {new_user}\n🔢 السيريال: {new_serial}\n🆔 ID: `{update.message.chat_id}`",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.message.chat_id != GROUP_ID: return
    
    if query.from_user.username not in ADMIN_USERNAMES:
        await query.answer("⛔ ليس لديك صلاحية!", show_alert=True)
        return

    await query.answer()
    data = query.data.split("_")
    action, user_chat_id = data[0], data[1]
    
    new_user = context.bot_data.get(f"u_{user_chat_id}")
    new_serial = context.bot_data.get(f"s_{user_chat_id}")
    is_update = context.bot_data.get(f"is_update_{user_chat_id}")

    if action == "exec":
        if not is_update:
            success = await process_list(query, context, user_chat_id, new_user, new_serial)
            if success:
                await query.message.delete()
                await context.bot.send_message(chat_id=GROUP_ID, text=f"✅ تم القبول والإضافة لليوزر: {new_user} بواسطة @{query.from_user.username}")
        else:
            keyboard = [[InlineKeyboardButton("🔄 تعديل يوزر", callback_data=f"edituser_{user_chat_id}"),
                         InlineKeyboardButton("🔄 تعديل تسلسلي", callback_data=f"editserial_{user_chat_id}")]]
            await query.edit_message_caption(caption=f"{query.message.caption}\n\n⚠️ البيانات موجودة، اختر نوع التعديل:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif action in ["edituser", "editserial"]:
        success = await process_list(query, context, user_chat_id, new_user, new_serial, edit_type=action)
        if success:
            await query.message.delete()
            await context.bot.send_message(chat_id=GROUP_ID, text=f"✅ تم التعديل والمسح لليوزر: {new_user} بواسطة @{query.from_user.username}")

    elif action == "reject":
        # طلب سبب الرفض من المشرف
        await context.bot.send_message(
            chat_id=GROUP_ID, 
            text=f"❌ يرجى الرد على هذه الرسالة بذكر **سبب الرفض** لليوزر {new_user}:\n(الآيدي المرتبط: `{user_chat_id}`)",
            reply_markup=ForceReply(selective=True)
        )

async def handle_reply_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # التأكد أن الرد في الجروب ومن مشرف
    if update.message.chat_id != GROUP_ID or not update.message.reply_to_message: return
    if update.message.from_user.username not in ADMIN_USERNAMES: return

    reply_text = update.message.reply_to_message.text
    if "سبب الرفض" in reply_text:
        # استخراج الآيدي من الرسالة الأصلية
        try:
            target_user_id = re.search(r"🆔 ID: `(\d+)`|المرتبط: `(\d+)`", reply_text + (update.message.reply_to_message.caption or ""))
            user_id = target_user_id.group(1) or target_user_id.group(2)
            reason = update.message.text
            
            await context.bot.send_message(chat_id=int(user_id), text=f"❌ نعتذر، تم رفض طلبك.\n**سبب الرفض:** {reason}")
            await update.message.reply_text("✅ تم إرسال سبب الرفض للاعب بنجاح.")
        except:
            await update.message.reply_text("❌ حدث خطأ في استخراج آيدي اللاعب.")

async def process_list(query, context, user_chat_id, new_user, new_serial, edit_type=None):
    try:
        channel_msg = await context.bot.forward_message(chat_id=query.message.chat_id, from_chat_id=CHANNEL_USERNAME, message_id=LIST_MESSAGE_ID)
        content = channel_msg.text
        await context.bot.delete_message(chat_id=query.message.chat_id, message_id=channel_msg.message_id)

        lines = content.split('\n')
        updated = False
        
        for i, line in enumerate(lines):
            # استخراج رقم السطر (م)
            prefix_match = re.match(r"^(\d+)\s*-\s*\[", line)
            if not prefix_match: continue
            line_number = prefix_match.group(1)

            # 1. حالة التعديل (يوزر أو سيريال)
            if edit_type == "edituser" and new_serial.lower() in line.lower():
                lines[i] = f"{line_number}- [ {new_user} | {new_serial} ]"
                updated = True
                break
            elif edit_type == "editserial" and new_user.lower() in line.lower():
                lines[i] = f"{line_number}- [ {new_user} | {new_serial} ]"
                updated = True
                break

            # 2. حالة الإضافة الجديدة (البحث عن أول خانة فارغة [   ])
            elif edit_type is None:
                # استخدام regex للبحث عن أقواس فارغة تماماً حتى لو فيها مسافات كتيرة
                if re.search(r"\[\s+\]", line) or "[]" in line.replace(" ", ""):
                    lines[i] = f"{line_number}- [ {new_user} | {new_serial} ]"
                    updated = True
                    break
        
        if updated:
            new_text = "\n".join(lines)
            await context.bot.edit_message_text(chat_id=CHANNEL_USERNAME, message_id=LIST_MESSAGE_ID, text=new_text)
            await context.bot.send_message(chat_id=user_chat_id, text="✅ مبروك! تم قبول طلبك وتسجيل بياناتك في القائمة.")
            return True
        else:
            await context.bot.send_message(chat_id=GROUP_ID, text="❌ فشل: لم يتم العثور على خانة فارغة في القائمة!")
            return False

    except Exception as e:
        await context.bot.send_message(chat_id=GROUP_ID, text=f"❌ خطأ تقني: {e}")
        return False

def main():
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, handle_registration))
    application.add_handler(CallbackQueryHandler(button_callback))
    # هاندلر للرد على سبب الرفض
    application.add_handler(MessageHandler(filters.TEXT & filters.REPLY, handle_reply_reason))
    
    application.run_polling()

if __name__ == '__main__':
    main()
