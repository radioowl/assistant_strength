from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery

ADMIN_IDS = [7254088454]  # Ваши ID администраторов
DOCUMENTATION_FILE = 'data.docx'  # Путь к файлу документации
PROMOTIONS = []  # Список для хранения акций

def admin_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Добавить акцию", callback_data='add_promotion'))
    keyboard.add(InlineKeyboardButton("Просмотр акций", callback_data='view_promotions'))
    keyboard.add(InlineKeyboardButton("Загрузить новый документ", callback_data='upload_document'))
    return keyboard

def admin_panel(bot: TeleBot):
    @bot.message_handler(commands=['admin'])
    def handler(message: Message):
        if message.from_user.id in ADMIN_IDS:
            bot.send_message(
                message.chat.id,
                "Добро пожаловать в админ-панель!\nВыберите действие:",
                reply_markup=admin_keyboard()
            )
        else:
            bot.send_message(message.chat.id, "У вас нет доступа к админ-панели.")

    @bot.callback_query_handler(func=lambda call: call.data == 'add_promotion')
    def add_promotion(call: CallbackQuery):
        if call.from_user.id in ADMIN_IDS:
            bot.send_message(call.message.chat.id, "Введите текст акции:")
            bot.register_next_step_handler(call.message, process_add_promotion)
        else:
            bot.answer_callback_query(call.id, "У вас нет доступа к этой команде.")

    def process_add_promotion(message: Message):
        if message.from_user.id in ADMIN_IDS:
            promotion_text = message.text
            PROMOTIONS.append(promotion_text)
            bot.send_message(message.chat.id, f"Акция добавлена: {promotion_text}")
        else:
            bot.send_message(message.chat.id, "У вас нет доступа к этой команде.")

    @bot.callback_query_handler(func=lambda call: call.data == 'view_promotions')
    def view_promotions(call: CallbackQuery):
        if call.from_user.id in ADMIN_IDS:
            if PROMOTIONS:
                promotions_text = "\n".join([f"{idx+1}. {promo}" for idx, promo in enumerate(PROMOTIONS)])
                bot.send_message(call.message.chat.id, f"Текущие акции:\n{promotions_text}")
            else:
                bot.send_message(call.message.chat.id, "Акций пока нет.")
        else:
            bot.answer_callback_query(call.id, "У вас нет доступа к этой команде.")

    @bot.callback_query_handler(func=lambda call: call.data == 'upload_document')
    def upload_document(call: CallbackQuery):
        if call.from_user.id in ADMIN_IDS:
            bot.send_message(call.message.chat.id, "Пожалуйста, отправьте новый файл .docx.")
            bot.register_next_step_handler(call.message, process_file_upload)
        else:
            bot.answer_callback_query(call.id, "У вас нет доступа к этой команде.")

    def process_file_upload(message: Message):
        """Обрабатывает загрузку нового файла .docx."""
        if message.document:
            doc_file = message.document

            # Проверяем тип файла
            if doc_file.mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                file_info = bot.get_file(doc_file.file_id)
                downloaded_file = bot.download_file(file_info.file_path)

                # Сохраняем файл, заменяя старый
                with open(DOCUMENTATION_FILE, 'wb') as new_file:
                    new_file.write(downloaded_file)
                
                bot.send_message(message.chat.id, "Новый документ успешно загружен и заменен.")
            else:
                bot.send_message(message.chat.id, "Пожалуйста, загрузите файл в формате .docx.")
        else:
            bot.send_message(message.chat.id, "Не удалось получить файл. Пожалуйста, попробуйте еще раз.")

    # Обработчик для получения файла
    @bot.message_handler(content_types=['document'])
    def handle_document(message: Message):
        if message.from_user.id in ADMIN_IDS:
            process_file_upload(message)
        else:
            bot.send_message(message.chat.id, "У вас нет доступа к этой команде.")

# Пример инициализации бота
if __name__ == '__main__':
    BOT_TOKEN = 'YOUR_BOT_TOKEN'
    bot = TeleBot(BOT_TOKEN)
    admin_panel(bot)
    bot.polling()
