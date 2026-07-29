from aiogram.types import BotCommand, KeyboardButton

from app.common.config import settings

COMMAND_DESCRIPTIONS = {
    "/support": "Обращение в поддержку",
    "/vacancy": "Посмотреть вакансии",
}

BOT_COMMANDS: list[BotCommand] = [
    BotCommand(command=command, description=COMMAND_DESCRIPTIONS[command])
    for command in COMMAND_DESCRIPTIONS
]

MAIN_MENU_KEYBOARD_MARKUP: list[list[KeyboardButton]] = [
    [KeyboardButton(text=command.description) for command in BOT_COMMANDS]
]

WELCOME_MESSAGE = "Добро пожаловать!"

MAIN_MENU_MESSAGE = """
Выберите нужный пункт меню:
"""

MAIN_MENU_BUTTON_TEXT = "📋 Главное меню"

SUPPORT_TICKET_CLOSED_EMOJI_ID = "5237699328843200968"  # ✅
SUPPORT_TICKED_OPENED_EMOJI_ID = "5312241539987020022"  # 🔥
SUPPORT_ANSWER_DELIVERED_EMOJI = "⚡"
CLOSE_SUPPORT_BUTTON_TEXT = "❌ Закрыть обращение"
START_SUPPORT_MESSAGE = """
Пожалуйста, опишите проблему
"""
WAIT_SUPPORT_MESSAGE = """
Мы получили обращение и ответим в течение 48 часов. Чтобы дополнить обращение, напишите в этот чат
"""
SUPPORT_TOPIC_NAME_TEMPLATE = "{username}: обращение"
CLOSE_TICKET_CONFIRMATION_MESSAGE = """
Обращение закрыто
"""
TICKET_CLOSED_BY_USER_MESSAGE = """
Обращение закрыто пользователем
"""
TICKET_CLOSED_AFTER_USER_BANNED_BOT_MESSAGE = """
Пользователь заблокировал бота. Тикет закрыт автоматически
"""
TICKET_CLOSED_BY_SUPPORT_MESSAGE = """
Ваше обращение закрыто сотрудником техподдержки
"""


TELEGRAM_BASE_URL = "https://t.me"

BACK_BUTTON_TEXT = "Назад"
SKIP_BUTTON_TEXT = "Пропустить"

# Vacancy Form Start
STARTING_VACANCY_FORM_MESSAGE = f"""
Наши вакансии размещены на сайте: {settings.frontend_vacancies_base_url}
Вы можете отправить отклик там же или через бота
"""
CHOOSE_VACANCY_MESSAGE = "Выберите вакансию или введите свою:"
SEND_NAME_MESSAGE = "Как вас зовут?"
SEND_TELEGRAM_MESSAGE = "Пожалуйста, оставьте ваш телеграм ⬇️"
SEND_RESUME_MESSAGE = (
    "Пожалуйста, загрузите ваше резюме одним файлом в формате PDF (до 10 MiB) ⬇️"
)
SEND_INFO_MESSAGE = "Почти готово. Можете оставить для нас сообщение 🙂"
VACANCY_FORM_FINAL_MESSAGE = "Спасибо! Мы получили ваш отклик и рассмотрим его"
VACANCY_NO_DOCUMENT_MESSAGE = f"В сообщении не прикреплён файл. {SEND_RESUME_MESSAGE}"
VACANCY_UNSUPPORTED_DOCUMENT_TYPE_MESSAGE = f"Неверный тип файла. {SEND_RESUME_MESSAGE}"
VACANCY_DOCUMENT_TOO_LARGE_MESSAGE = f"Слишком большой файл. {SEND_RESUME_MESSAGE}"
VACANCY_INVALID_INPUT_TYPE_MESSAGE = """
Пожалуйста, используйте только текстовые сообщения или кнопки для заполнения формы вакансии
"""

CONTINUE_IN_BOT_KEYBOARD_TEXT = "Продолжить через бота"
VACANCY_FORM_EPILOGUE_KEYBOARD_MARKUP: list[list[KeyboardButton]] = [
    [
        KeyboardButton(text=CONTINUE_IN_BOT_KEYBOARD_TEXT),
        KeyboardButton(text=MAIN_MENU_BUTTON_TEXT),
    ],
]

NAVIGATION_KEYBOARD_MARKUP: list[list[KeyboardButton]] = [
    [KeyboardButton(text=BACK_BUTTON_TEXT), KeyboardButton(text=MAIN_MENU_BUTTON_TEXT)]
]

NAVIGATION_KEYBOARD_MARKUP_WITH_SKIP: list[list[KeyboardButton]] = [
    [KeyboardButton(text=SKIP_BUTTON_TEXT)],
    *NAVIGATION_KEYBOARD_MARKUP,
]

SPECIALIZATION_ROWS: list[list[str]] = [
    ["Frontend разработчик", "Backend разработчик"],
    ["QA Engineer (Тестировщик)", "Automation QA (Автотестер)"],
    ["Графический дизайнер", "Product manager"],
    ["SMM-специалист", "Marketing-специалист"],
    ["Копирайтер/Редактор"],
]
CHOOSE_SPECIALIZATION_KEYBOARD_MARKUP: list[list[KeyboardButton]] = [
    *[
        [KeyboardButton(text=specialization) for specialization in specialization_row]
        for specialization_row in SPECIALIZATION_ROWS
    ],
    *NAVIGATION_KEYBOARD_MARKUP,
]

LEAVE_CURRENT_ACCOUNT_BUTTON_TEXT = "Оставить для связи текущий аккаунт"
SEND_TELEGRAM_KEYBOARD_MARKUP: list[list[KeyboardButton]] = [
    [KeyboardButton(text=LEAVE_CURRENT_ACCOUNT_BUTTON_TEXT)],
    *NAVIGATION_KEYBOARD_MARKUP,
]
# Vacancy Form End
