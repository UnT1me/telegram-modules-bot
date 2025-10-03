🤖 Telegram Modules Tracking Bot

Телеграм-бот для учёта выполненных модулей с автоматическим расчётом баллов и денежного эквивалента. Поддерживает группы до 40 пользователей с индивидуальным учётом, аналитикой и лидербордом.

⭐ Основные возможности

🎯 Учёт модулей





Добавление модулей через интерактивные кнопки (/modules)



Быстрое добавление через команды (/add BMU 5X 3)



Поддержка дробных баллов (14.5 баллов)



Возможность отмены последнего действия



Множественное выполнение одного модуля в день

📊 Аналитика и отчёты





Личная статистика: баллы и деньги за месяц (/points)



Графики: визуализация прогресса по дням (/graph)



ИИ-анализ: персонализированные инсайты и советы (/insight)



Лидерборд: топ-20 пользователей (/leaderboard)

🔧 Автоматизация





Ежедневные напоминания в 18:00



Месячные отчёты 1-го числа в 10:00



Автоматический расчёт: баллы × 220₽

👑 Админ-панель





Просмотр всех пользователей и их статистики



Ручная отправка отчётов



Управление системой



Детальная аналитика по пользователям

⏰ Временные ограничения

Добавление модулей доступно только с 18:00 до 23:59 (настраивается).

🏗️ Архитектура

Технологический стек





Python 3.9+



aiogram 3.x - современный фреймворк для Telegram ботов



PostgreSQL через Supabase - облачная база данных



matplotlib - генерация графиков



asyncio - асинхронное выполнение задач

Структура проекта

telegram-modules-bot/
├── main.py              # Точка входа
├── config.py            # Конфигурация
├── database.py          # Модели данных и работа с БД
├── middleware.py        # Ограничения по времени
├── handlers.py          # Основные команды бота
├── advanced_handlers.py # Графики, аналитика, лидерборд
├── admin_handlers.py    # Админ-панель
├── scheduler.py         # Автоматические задачи
├── utils.py             # Вспомогательные функции
├── requirements.txt     # Зависимости
└── README.md           # Документация


🚀 Быстрый старт

1. Клонирование и установка

git clone <repository-url>
cd telegram-modules-bot
pip install -r requirements.txt


2. Настройка окружения

Скопируйте .env.example в .env и заполните:

BOT_TOKEN=your_telegram_bot_token
DATABASE_URL=postgresql://user:password@host:port/database
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
TIMEZONE=Europe/Moscow
ADMIN_IDS=123456789,987654321


3. Настройка базы данных

Создайте базу данных PostgreSQL (например, в Supabase) и выполните SQL:

-- Таблицы создаются автоматически при первом запуске
-- Но вы можете создать их заранее:

CREATE TABLE modules (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    points NUMERIC NOT NULL
);

CREATE TABLE user_module_logs (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    module_id INT NOT NULL REFERENCES modules(id),
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE admins (
    user_id BIGINT PRIMARY KEY
);

CREATE TABLE monthly_summary (
    user_id BIGINT,
    year INT,
    month INT,
    total_points NUMERIC,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, year, month)
);


4. Запуск бота

python main.py


📋 Команды бота







Команда



Описание





/start



Приветствие и справка





/modules



Интерактивный выбор модулей





/add <название> [количество]



Быстрое добавление





/points



Баллы за текущий месяц





/graph



График выполнения





/insight



ИИ-анализ прогресса





/leaderboard



Топ-20 пользователей





/admin



Админ-панель (только для админов)





/admin_user <user_id>



Статистика пользователя

Примеры использования

/add BMU 5X          # Добавить 1 выполнение
/add BMU 5X 3        # Добавить 3 выполнения
/add Практика 1      # Добавить модуль "Практика 1"


📊 База данных

Модули по умолчанию





BMU 5X - 14.5 баллов



BMU 10X - 29.0 баллов



Практика 1 - 10.0 баллов



Практика 2 - 15.0 баллов



Теория - 8.0 баллов



Дополнительный модуль - 12.5 баллов

Схема данных





modules: справочник модулей с баллами



user_module_logs: лог выполненных модулей



admins: список администраторов



monthly_summary: месячные итоги пользователей

⚙️ Конфигурация

Основные параметры (config.py)

ALLOWED_HOUR_START = 18      # Начало разрешённого времени
ALLOWED_HOUR_END = 23        # Конец разрешённого времени
POINTS_TO_MONEY_RATE = 220   # Курс: баллы → рубли


Автоматизация





Напоминания: ежедневно в 18:00



Отчёты: 1-го числа в 10:00



Часовой пояс: настраивается в .env

🔒 Безопасность

Администраторы





Настройка в переменной ADMIN_IDS



Дополнительные админы через базу данных



Ограниченный доступ к админ-функциям

Данные





SSL-подключение к PostgreSQL



Логирование действий



Валидация пользовательского ввода

📈 Мониторинг

Логирование





Все действия записываются в bot.log



Уровни: INFO, WARNING, ERROR



Ротация логов по размеру

Метрики





Количество активных пользователей



Общие баллы системы



Статистика по модулям

🚀 Развёртывание

VPS/Сервер





Установите Python 3.9+ и зависимости



Настройте PostgreSQL или используйте Supabase



Создайте systemd сервис:

[Unit]
Description=Telegram Modules Bot
After=network.target

[Service]
Type=simple
User=botuser
WorkingDirectory=/path/to/telegram-modules-bot
ExecStart=/usr/bin/python3 main.py
Restart=always

[Install]
WantedBy=multi-user.target


Docker (опционально)

FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]


🛠️ Разработка

Структура кода





Модульность: каждый файл отвечает за свою область



Асинхронность: все операции неблокирующие



Обработка ошибок: комплексный try-catch



Типизация: аннотации типов для лучшей читаемости

Расширение функционала





Новые модули добавляйте в DEFAULT_MODULES



Новые команды - в соответствующий handler



Бизнес-логику выносите в отдельные функции

📞 Поддержка

Частые проблемы





"База данных недоступна" - проверьте DATABASE_URL



"Бот не отвечает" - убедитесь, что токен корректный



"Время недоступно" - проверьте часовой пояс

Логи и диагностика

tail -f bot.log                    # Просмотр логов
grep ERROR bot.log                 # Поиск ошибок


📄 Лицензия

MIT License - можете использовать в коммерческих проектах.

🤝 Вклад в проект





Fork репозитория



Создайте feature branch



Commit ваши изменения



Push в branch



Создайте Pull Request



Версия: 1.0.0
Автор: [Ваше имя]
Последнее обновление: 2025-01-01
