# 🚀 Deployment Guide

Quick Deploy on VPS

1. Server Setup

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.9+
sudo apt install python3 python3-pip python3-venv git -y

# Clone repository
git clone https://github.com/YOUR_USERNAME/telegram-modules-bot.git
cd telegram-modules-bot


2. Environment Setup

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env  # Edit with your credentials


3. Database Setup (Supabase)





Create account at https://supabase.com



Create new project



Copy connection details to .env



Tables will be created automatically on first run

4. Telegram Bot Setup





Message @BotFather on Telegram



Create new bot: /newbot



Copy token to .env file



Set webhook (optional for VPS)

5. Run Bot

# Test run
python main.py

# Production run with systemd
sudo cp telegram-modules-bot.service /etc/systemd/system/
sudo systemctl enable telegram-modules-bot
sudo systemctl start telegram-modules-bot


6. Monitoring

# Check status
sudo systemctl status telegram-modules-bot

# View logs
tail -f bot.log
journalctl -u telegram-modules-bot -f


Environment Variables Required

BOT_TOKEN=your_telegram_bot_token
DATABASE_URL=postgresql://user:password@host:port/database
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
TIMEZONE=Europe/Moscow
ADMIN_IDS=123456789,987654321


System Requirements





Python 3.9+



PostgreSQL access (Supabase recommended)



512MB RAM minimum



1GB disk space



Stable internet connection

Security Checklist





Set strong database password



Configure firewall (allow only necessary ports)



Keep .env file private (never commit to git)



Regular system updates



Monitor logs for suspicious activity



Backup database regularly

Troubleshooting

Common Issues:





Database connection failed: Check DATABASE_URL in .env



Bot doesn't respond: Verify BOT_TOKEN



Time restrictions not working: Check TIMEZONE setting



Permission denied: Ensure correct file permissions

Support Commands:

# Check Python version
python3 --version

# Test database connection
python3 -c "import asyncpg; print('AsyncPG installed')"

# Verify bot token
python3 -c "from config import BOT_TOKEN; print('Token loaded' if BOT_TOKEN else 'Token missing')"




Created by: Telegram Modules Bot v1.0
Last updated: 2025-01-01
