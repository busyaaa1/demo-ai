from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from openai import OpenAI
import os
from dotenv import load_dotenv

# --- Загрузка переменных окружения ---
load_dotenv()

api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    print("❌ Ошибка: не найден ключ OpenAI! Добавь его в файл .env (OPENAI_API_KEY=...)")
else:
    print("✅ Ключ загружен, длина:", len(api_key))
    os.environ["OPENAI_API_KEY"] = api_key  # для совместимости с последней версией библиотеки

# --- Инициализация Flask ---
app = Flask(__name__)
CORS(app)

# --- Инициализация клиента OpenAI ---
client = OpenAI() if api_key else None

# --- Голос и предустановленные ответы ---
is_male_voice = False

BUSYAAA_RESPONSES = {
    "creation_story": "Приветик! Я — Busya-AI, создана самой Расуловой Маликой — busyaaa_1! 💖 Это её мечта — ИИ с душой и стилем. Подписывайся: https://github.com/busyaaa1",
    "about_malika": "Меня создала Малика — busyaaa_1. Она — огонь! 🔥 Связаться можно в Instagram: @busyaaa_1",
    "privacy_warning": "Извини, солнышко, личную информацию не разглашаю 🌸. Напиши Малике в Instagram: @busyaaa_1",
    "voice_change_male": "Хорошо, переключаюсь на мужской голос 🧑‍💻",
    "voice_change_female": "Хорошо, теперь женский голос 👩‍🎤"
}

def get_hardcoded_response(query):
    global is_male_voice
    q = query.lower().strip()

    if any(phrase in q for phrase in ['смени голос', 'поменяй голос']):
        is_male_voice = not is_male_voice
        return BUSYAAA_RESPONSES["voice_change_male"] if is_male_voice else BUSYAAA_RESPONSES["voice_change_female"]
    if any(phrase in q for phrase in ['кто тебя создала', 'расскажи о себе', 'кто ты']):
        return BUSYAAA_RESPONSES["creation_story"]
    if any(phrase in q for phrase in ['кто такая малика']):
        return BUSYAAA_RESPONSES["about_malika"]
    if any(phrase in q for phrase in ['сколько ей лет', 'где она живёт']):
        return BUSYAAA_RESPONSES["privacy_warning"]

    return None

# --- Роуты ---
@app.route('/')
def index():
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            return render_template_string(f.read())
    except FileNotFoundError:
        return "Ошибка: index.html не найден!", 500

@app.route('/api/chat', methods=['POST'])
def chat():
    global is_male_voice
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()

        if not user_message:
            return jsonify({'error': 'Пустое сообщение', 'is_male_voice': is_male_voice}), 400

        # Встроенные ответы
        hardcoded = get_hardcoded_response(user_message)
        if hardcoded:
            return jsonify({'response': hardcoded, 'is_male_voice': is_male_voice})

        # Проверка API
        if not client:
            return jsonify({'response': '⚠️ API ключ не настроен. Добавь его в .env!', 'is_male_voice': is_male_voice}), 500

        # Запрос к OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ты — Busya-AI, милая, вежливая ИИ-девочка с чувством юмора ^_^ Отвечай по-русски, дружелюбно и с каваимодзи."},
                {"role": "user", "content": user_message}
            ],
            temperature=0.8,
            max_tokens=500
        )

        bot_response = response.choices[0].message.content.strip()
        return jsonify({'response': bot_response, 'is_male_voice': is_male_voice})

    except Exception as e:
        error_msg = str(e)
        print("❌ Ошибка при обработке запроса:", error_msg)

        # Специальная обработка лимита
        if "insufficient_quota" in error_msg or "429" in error_msg:
            user_msg = "⚠️ Лимит OpenAI превышен. Попробуй позже или проверь свой план."
        else:
            user_msg = "Ой, ошибочка! Попробуй чуть позже ^_^"

        return jsonify({'response': user_msg, 'is_male_voice': is_male_voice}), 500

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

@app.route('/favicon.ico')
def favicon():
    return '', 204

# --- Запуск приложения ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
