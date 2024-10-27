
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
import random
from fuzzywuzzy import fuzz

BOT_TOKEN = '7732393943:AAHEuk-i1hj-Ip7zR3hfjM5SrRAxkmZ0wtw'
IAM_TOKEN = 't1.9euelZqdxpzKio6PjY2eiZXNiYyPyu3rnpWanZ2OjZWKjZiUyorHlpTImpDl8_dFYAhH-e80CD18_N3z9wUPBkf57zQIPXz8zef1656VmoqZlpKQmY7Mx5aWyJuRkJ2X7_zF656VmoqZlpKQmY7Mx5aWyJuRkJ2X.ooySk_GOoRiDGZ342gOEp764Kv1MipxVcL4_z1zbAV7rpw3MssRtu-hYPk4LV8hKu2Ee42iCzqBwTEhdUN49DA'

DOCUMENTATION_FILE = 'data.docx'  # Путь к файлу документации
IMAGE_DIR = 'images/'  # Директория для хранения изображений

class States:
    base = 'base'
    ask_question = 'ask_question'

state_storage = StateMemoryStorage()
bot = telebot.TeleBot(BOT_TOKEN, state_storage=state_storage)

DOCUMENTATION_INDEX = {}

def load_documentation(doc_file: str):
    global DOCUMENTATION_INDEX
    DOCUMENTATION_INDEX.clear()

    try:
        doc = Document(doc_file)
        current_section = ""
        
        for paragraph in doc.paragraphs:
            if paragraph.style.name.startswith("Heading"):
                current_section = paragraph.text.strip()
                DOCUMENTATION_INDEX[current_section] = {"text": [], "images": [], "keywords": set()}
            elif current_section:
                DOCUMENTATION_INDEX[current_section]["text"].append(paragraph.text.strip())
                DOCUMENTATION_INDEX[current_section]["keywords"].update(paragraph.text.strip().split())

    except Exception as e:
        print(f'Ошибка при загрузке документации: {e}')

def find_and_remove_images(text, used_images):
    images = []
    pattern = r"Рисунок\s*(\d+)"
    
    def replace_image_match(match):
        image_number = match.group(1)
        image_path = os.path.join(IMAGE_DIR, f"{image_number}.jpg")
        
        if os.path.isfile(image_path) and image_path not in used_images:
            images.append(image_path)
            used_images.add(image_path)
        
        return ""
    
    modified_text = re.sub(pattern, replace_image_match, text)
    return modified_text.strip(), images

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

def search_documentation(query: str, threshold=70):
    found_answers = []
    found_images = []
    used_images = set()  # Множество для отслеживания отправленных изображений

    for section, content in DOCUMENTATION_INDEX.items():
        section_similarity = fuzz.partial_ratio(query.lower(), section.lower())
        
        if section_similarity >= threshold:
            text, images = find_and_remove_images(" ".join(content["text"]), used_images)
            found_answers.append(f"{section}:\n{text}")
            found_images.extend(images)
            continue
        
        for text in content["text"]:
            text_similarity = fuzz.partial_ratio(query.lower(), text.lower())
            if text_similarity >= threshold:
                modified_text, images = find_and_remove_images(text, used_images)
                found_answers.append(f"{section}:\n{modified_text}")
                found_images.extend(images)
                break
    
    return "\n\n".join(found_answers), found_images

prepared_phrases = [
    "Кстати, не забывай про акцию на ноутбуки от компании 'СИЛА!'",
    "А ты уже выбрал ноутбук от компании СИЛА?",
    "Между прочим, ты можешь успеть купить себе ноутбук от СИЛА :D",
    "Не забывай, что именно от компании СИЛА ты сможешь получить наивысшие технологии!",
    "Технологии — это СИЛА!",
]

@bot.message_handler(commands=['start'])
def start(message: Message) -> None:
    bot.send_message(
        message.chat.id,
        'Привет! Я бот Яндекс.GPT. Задайте мне вопрос, и я постараюсь помочь!'
    )
    bot.set_state(message.from_user.id, States.base, message.chat.id)

@bot.message_handler(commands=['admin'])
def admin_command(message: Message):
    print(f"Пользователь {message.from_user.id} пытается получить доступ к админ-панели.")
    if message.from_user.id in [7254088454]:  # Проверьте ID администратора
        admin_panel(bot)  # Вызываем админ-панель
        print("Доступ к админ-панели предоставлен.")
    else:
        bot.send_message(message.chat.id, "У вас нет доступа к админ-панели.")
        print("Попытка доступа к админ-панели отклонена.")

@bot.message_handler(state=States.base)
def ask_question(message: Message) -> None:
    question = message.text

    # Регулируем точность (fuzziness)
    doc_answer, images = search_documentation(question, threshold=80)
    if doc_answer:
        response_message = f"Ответ из документации:\n{doc_answer}"
        bot.send_message(message.chat.id, response_message)
        send_images(message.chat.id, images)  # Отправляем изображения
    else:
        response_message = "Ответ в документации не найден. Пожалуйста, свяжитесь с разработчиками для получения помощи."
        bot.send_message(message.chat.id, response_message)

    if random.random() < 0.4:
        phrase = random.choice(prepared_phrases)
        bot.send_message(message.chat.id, phrase)

    bot.send_message(message.chat.id, 'Задайте другой вопрос, если хотите.')

if __name__ == '__main__':
    bot.add_custom_filter(custom_filters.StateFilter(bot))
    load_documentation(DOCUMENTATION_FILE)
    admin_panel(bot)  # Инициализируем админ-панель
    bot.polling()
