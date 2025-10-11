#!/bin/bash

# Deployment script for remdepo_bot
# This script is run on the server during CI/CD deployment

set -e  # Exit on any error

echo "🚀 Starting deployment..."

# Navigate to project directory
cd /path/to/your/remdepo_bot

# Stop the bot
echo "⏹️ Stopping bot..."
sudo systemctl stop remdepo-bot || true

# Backup database
echo "💾 Backing up database..."
cp bot.db bot.db.backup.$(date +%Y%m%d_%H%M%S) || true

# Pull latest changes
echo "📥 Pulling latest changes..."
git pull origin main

# Install/update dependencies
echo "📦 Installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt

# Run database migrations (if needed)
echo "🗄️ Running database migrations..."
python -c "
import asyncio
from bot.database.engine import init_db

async def migrate():
    await init_db()
    print('Database initialized successfully')

asyncio.run(migrate())
" || echo "⚠️ Database migration failed, but continuing..."

# Start the bot
echo "▶️ Starting bot..."
sudo systemctl start remdepo-bot

# Wait a moment and check status
sleep 5
echo "🔍 Checking bot status..."
sudo systemctl status remdepo-bot --no-pager

echo "✅ Deployment completed!"
