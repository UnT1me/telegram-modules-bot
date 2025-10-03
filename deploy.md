# 🚀 Руководство по развертыванию 
### Быстрое развертывание на VPS

### Обновите систему 
- sudo apt update && sudo apt upgrade -y

### Установите Python 3.9+ 
- sudo apt install python3 python3-pip python3-venv git -y

### Клонируйте репозиторий 
- git clone https://github.com/UnT1me/telegram-modules-bot.git
- cd telegram-modules-bot
 
### Настройка окружения 
Создайте виртуальное окружение 
- python3 -m venv venv
- source venv/bin/activate

### Установите зависимости 
pip install -r requirements.txt

### Настройте переменные окружения 
- cp .env.example .env
- nano .env  # Отредактируйте файл, указав свои учетные данные
 
### Настройка базы данных (Supabase) 

    Создайте аккаунт на https://supabase.com 
    Создайте новый проект
    Скопируйте данные подключения в файл .env
    Таблицы будут созданы автоматически при первом запуске
     
### Настройка Telegram-бота 

    Напишите @BotFather  в Telegram
    Создайте нового бота: /newbot
    Скопируйте токен в файл .env
    При необходимости настройте вебхук (опционально для VPS)
     
### Запуск бота 
python main.py
 
### Запуск в продакшене через systemd 
- sudo cp telegram-modules-bot.service /etc/systemd/system/
- sudo systemctl enable telegram-modules-bot
- sudo systemctl start telegram-modules-bot
 
 
### Мониторинг 
Проверить статус 
- sudo systemctl status telegram-modules-bot
 
 

### Просмотр логов 
- tail -f bot.log
- journalctl -u telegram-modules-bot -f
 
 
 
### Обязательные переменные окружения 
```
env
BOT_TOKEN=ваш_токен_telegram_бота
DATABASE_URL=postgresql://пользователь:пароль@хост:порт/база_данных
SUPABASE_URL=ваш_supabase_url
SUPABASE_KEY=ваш_supabase_key
TIMEZONE=Europe/Moscow
ADMIN_IDS=123456789,987654321
```  
### Системные требования 

    Python 3.9+
    Доступ к PostgreSQL (рекомендуется Supabase)
    Минимум 512 МБ ОЗУ
    1 ГБ дискового пространства
    Стабильное интернет-соединение
     

 
### Чек-лист безопасности 

    Установите надежный пароль для базы данных
    Настройте брандмауэр (разрешите только необходимые порты)
    Храните файл .env в секрете (никогда не коммитьте его в Git!)
    Регулярно обновляйте систему
    Следите за логами на предмет подозрительной активности
    Регулярно делайте резервные копии базы данных
     

 
### Устранение неполадок 
Распространённые проблемы: 

    Не удается подключиться к базе данных: проверьте DATABASE_URL в .env
    Бот не отвечает: убедитесь, что BOT_TOKEN указан верно
    Не работают временные ограничения: проверьте настройку TIMEZONE
    Отказ в доступе: убедитесь, что права на файлы выставлены корректно
     

### Команды для диагностики: 

Проверить версию Python 
- python3 --version
 
 

### Проверить подключение к базе данных 
- python3 -c "import asyncpg; print('AsyncPG установлен')"
 
 
### Проверить токен бота 
- python3 -c "from config import BOT_TOKEN; print('Токен загружен' if BOT_TOKEN else 'Токен отсутствует')"


---

**Создано:** Telegram Modules Bot v1.0
**Последнее обновление:** 2025-01-01 
