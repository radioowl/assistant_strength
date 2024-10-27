from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery

# Список ID администраторов, которые имеют доступ к админ-панели
ADMIN_IDS = [5233246188]  # Ваши ID администраторов
# Путь к файлу документации
DOCUMENTATION_FILE = 'data.docx'  
# Список для хранения акций
PROMOTIONS = []  

def admin_keyboard():
    """Создает клавиатуру для админ-панели с кнопками."""
    keyboard = InlineKeyboardMarkup()
    # Кнопка для добавления акции
    keyboard.add(InlineKeyboardButton("Добавить акцию", callback_data='add_promotion'))
    # Кнопка для просмотра акций
    keyboard.add(InlineKeyboardButton("Просмотр акций", callback_data='view_promotions'))
    # Кнопка для загрузки нового документа
    keyboard.add(InlineKeyboardButton("Загрузить новый документ", callback_data='upload_document'))
    return keyboard

def admin_panel(bot: TeleBot):
    """Настраивает админ-панель для бота."""
    
    @bot.message_handler(commands=['admin'])
    def handler(message: Message):
        """Обрабатывает команду /admin, предоставляя доступ только администраторам."""
        if message.from_user.id in ADMIN_IDS:
            bot.send_message(
                message.chat.id,
                "Добро пожаловать в админ-панель!\nВыберите действие:",
                reply_markup=admin_keyboard()  # Отправляет клавиатуру админ-панели
            )
        else:
            bot.send_message(message.chat.id, "У вас нет доступа к админ-панели.")

    @bot.callback_query_handler(func=lambda call: call.data == 'add_promotion')
    def add_promotion(call: CallbackQuery):
        """Обрабатывает нажатие кнопки для добавления акции."""
        if call.from_user.id in ADMIN_IDS:
            bot.send_message(call.message.chat.id, "Введите текст акции:")  # Запрашивает текст акции
            bot.register_next_step_handler(call.message, process_add_promotion)  # Переходит к следующему шагу
        else:
            bot.answer_callback_query(call.id, "У вас нет доступа к этой команде.")

    def process_add_promotion(message: Message):
        """Обрабатывает добавление акции."""
        if message.from_user.id in ADMIN_IDS:
            promotion_text = message.text  # Получает текст акции из сообщения
            PROMOTIONS.append(promotion_text)  # Добавляет акцию в список
            bot.send_message(message.chat.id, f"Акция добавлена: {promotion_text}")  # Подтверждает добавление
        else:
            bot.send_message(message.chat.id, "У вас нет доступа к этой команде.")

    @bot.callback_query_handler(func=lambda call: call.data == 'view_promotions')
    def view_promotions(call: CallbackQuery):
        """Обрабатывает нажатие кнопки для просмотра акций."""
        if call.from_user.id in ADMIN_IDS:
            if PROMOTIONS:
                # Формирует текст с текущими акциями
                promotions_text = "\n".join([f"{idx+1}. {promo}" for idx, promo in enumerate(PROMOTIONS)])
                bot.send_message(call.message.chat.id, f"Текущие акции:\n{promotions_text}")  # Отправляет список акций
            else:
                bot.send_message(call.message.chat.id, "Акций пока нет.")  # Если акций нет, сообщает об этом
        else:
            bot.answer_callback_query(call.id, "У вас нет доступа к этой команде.")

    @bot.callback_query_handler(func=lambda call: call.data == 'upload_document')
    def upload_document(call: CallbackQuery):
        """Обрабатывает нажатие кнопки для загрузки нового документа."""
        if call.from_user.id in ADMIN_IDS:
            bot.send_message(call.message.chat.id, "Пожалуйста, отправьте новый файл .docx.")  # Запрашивает файл
            bot.register_next_step_handler(call.message, process_file_upload)  # Переходит к следующему шагу
        else:
            bot.answer_callback_query(call.id, "У вас нет доступа к этой команде.")

    def process_file_upload(message: Message):
        """Обрабатывает загрузку нового файла .docx."""
        if message.document:
            doc_file = message.document  # Получает файл из сообщения

            # Проверяем тип файла
            if doc_file.mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                file_info = bot.get_file(doc_file.file_id)  # Получает информацию о файле
                downloaded_file = bot.download_file(file_info.file_path)  # Загружает файл

                # Сохраняем файл, заменяя старый
                with open(DOCUMENTATION_FILE, 'wb') as new_file:
                    new_file.write(downloaded_file)  # Записывает новый файл на диск
                
                bot.send_message(message.chat.id, "Новый документ успешно загружен и заменен.")
            else:
                bot.send_message(message.chat.id, "Пожалуйста, загрузите файл в формате .docx.")  # Проверка на правильный формат
        else:
            bot.send_message(message.chat.id, "Не удалось получить файл. Пожалуйста, попробуйте еще раз.")

    # Обработчик для получения файла
    @bot.message_handler(content_types=['document'])
    def handle_document(message: Message):
        """Обрабатывает получение документа."""
        if message.from_user.id in ADMIN_IDS:
            process_file_upload(message)  # Переходит к обработке загрузки
        else:
            bot.send_message(message.chat.id, "У вас нет доступа к этой команде.")

# Пример инициализации бота
if __name__ == '__main__':
    BOT_TOKEN = 'YOUR_BOT_TOKEN'  # Токен вашего бота
    bot = TeleBot(BOT_TOKEN)  # Создает экземпляр бота
    admin_panel(bot)  # Инициализирует админ-панель
    bot.polling()  # Запускает бота
