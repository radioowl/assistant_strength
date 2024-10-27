import json
import telebot
from telebot.types import Message, InputMediaPhoto
from telebot import custom_filters
from telebot.storage import StateMemoryStorage
import requests
from docx import Document
import os
import re
from admin_panel import admin_panel  # Импортируйте админ-панель

BOT_TOKEN = '7732393943:AAHEuk-i1hj-Ip7zR3hfjM5SrRAxkmZ0wtw'
IAM_TOKEN = 't1.9euelZqVycuXkM2bmsiTno6clcbOm-3rnpWanZ2OjZWKjZiUyorHlpTImpDl9PcsXwlH-e8gX3is3fT3bA0HR_nvIF94rM3n9euelZqTx4mPzpaKz56XzouYm4nNy-_8xeuelZqTx4mPzpaKz56XzouYm4nNyw.fKMNJ-14zdVFsey9OFuE3y79RO4b76BDW02VozrlEqhKNujkT_BMtcwnJjAd1eb4iKEm05jcappQCXXOXC3FAg'

DOCUMENTATION_FILE = 'data.docx'  # Путь к файлу документации
IMAGE_DIR = 'images/'  # Директория для хранения изображений

# Состояния бота
class States:
    base = 'base'
    ask_question = 'ask_question'

state_storage = StateMemoryStorage()
bot = telebot.TeleBot(BOT_TOKEN, state_storage=state_storage)

DOCUMENTATION_INDEX = {}  # Словарь для хранения текста и связанных изображений

# Функция загрузки документации
def load_documentation(doc_file: str):
    global DOCUMENTATION_INDEX
    DOCUMENTATION_INDEX.clear()

    try:
        doc = Document(doc_file)
        current_section = ""
        
        for paragraph in doc.paragraphs:
            if paragraph.style.name.startswith("Heading"):
                current_section = paragraph.text.strip()
                DOCUMENTATION_INDEX[current_section] = {"text": [], "images": []}
            elif current_section:
                DOCUMENTATION_INDEX[current_section]["text"].append(paragraph.text.strip())

    except Exception as e:
        print(f'Ошибка при загрузке документации: {e}')

# Функция для поиска "Рисунок N" и получения соответствующих изображений
def find_images_from_text(text):
    images = []
    pattern = r"Рисунок\s*(\d+)"  # Регулярное выражение для поиска "Рисунок N"
    matches = re.findall(pattern, text)
    
    for match in matches:
        image_number = match
        image_path = os.path.join(IMAGE_DIR, f"{image_number}.jpg")
        
        if os.path.isfile(image_path):
            images.append(image_path)
            print(f"Найдено изображение: {image_path}")

    return images

# Функция для отправки изображений в альбомах
def send_images(chat_id, images):
    for i in range(0, len(images), 10):
        media_group = []
        for image_path in images[i:i + 10]:
            if os.path.isfile(image_path):
                try:
                    with open(image_path, 'rb') as img_file:
                        media_group.append(InputMediaPhoto(img_file.read()))
                except Exception as e:
                    print(f"Ошибка открытия файла {image_path}: {e}")

        if media_group:
            try:
                bot.send_media_group(chat_id, media_group)
            except Exception as e:
                print(f"Ошибка отправки изображений: {e}")

# Функция поиска в документации
def search_documentation(query: str):
    found_answers = []
    found_images = []

    for section, content in DOCUMENTATION_INDEX.items():
        if query.lower() in section.lower() or any(query.lower() in text.lower() for text in content["text"]):
            found_answers.append(f"{section}:\n" + "\n".join(content["text"]))
            found_images.extend(find_images_from_text(" ".join(content["text"])))

    return "\n\n".join(found_answers), found_images

@bot.message_handler(commands=['start'])
def start(message: Message) -> None:
    bot.send_message(
        message.chat.id,
        'Привет! Я бот Яндекс.GPT. Задайте мне вопрос, и я постараюсь помочь!'
    )
    bot.set_state(message.from_user.id, States.base, message.chat.id)

@bot.message_handler(commands=['admin'])  # Добавляем обработчик для команды /admin
def admin_command(message: Message):
    print(f"Пользователь {message.from_user.id} пытается получить доступ к админ-панели.")  # Отладочное сообщение
    if message.from_user.id in [7254088454]:  # Проверьте ID администратора
        admin_panel(bot)  # Вызываем админ-панель
        print("Доступ к админ-панели предоставлен.")  # Отладочное сообщение
    else:
        bot.send_message(message.chat.id, "У вас нет доступа к админ-панели.")
        print("Попытка доступа к админ-панели отклонена.")  # Отладочное сообщение

@bot.message_handler(state=States.base)
def ask_question(message: Message) -> None:
    question = message.text

    # Поиск ответа в документации
    doc_answer, images = search_documentation(question)
    if doc_answer:
        response_message = f"Ответ из документации:\n{doc_answer}"
        bot.send_message(message.chat.id, response_message)
        send_images(message.chat.id, images)
    else:
        # Если ничего не найдено в документации, обращаемся к Яндекс.GPT
        gpt_answer = ask_yandex_gpt(question)
        response_message = f"Ответ Яндекс GPT: {gpt_answer}"
        bot.send_message(message.chat.id, response_message)

    bot.send_message(message.chat.id, 'Задайте другой вопрос, если хотите.')

# Функция для запроса к Яндекс GPT
def ask_yandex_gpt(question: str) -> str:
    url = 'https://llm.api.cloud.yandex.net/foundationModels/v1/completion'
    headers = {
        'Authorization': f'Bearer {IAM_TOKEN}',
        'Content-Type': 'application/json'
    }
    data = {
        "modelUri": "gpt://b1gjp5vama10h4due384/yandexgpt/latest",
        "completionOptions": {
            "stream": False,
            "temperature": 1,
            "maxTokens": 2000
        },
        "messages": [
            {
                "role": "system",
                "text": "Ты — умный ассистент."
            },
            {
                "role": "user",
                "text": question
            }
        ]
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        api_response = response.json()
        answer = (
            api_response.get("result", {})
            .get("alternatives", [{}])[0]
            .get("message", {})
            .get("text", "Ответ не найден.")
        )
        return answer.strip()
    else:
        return "Ошибка при обращении к API."

if __name__ == '__main__':
    bot.add_custom_filter(custom_filters.StateFilter(bot))
    load_documentation(DOCUMENTATION_FILE)
    admin_panel(bot)  # Инициализируем админ-панель
    bot.polling()
