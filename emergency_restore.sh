#!/bin/bash

# 🚨 EMERGENCY DATABASE RESTORE SCRIPT
# Use this if deployment breaks your database

echo "🚨 EMERGENCY DATABASE RESTORE"
echo "================================"

# Stop the bot
echo "⏹️ Stopping bot..."
sudo systemctl stop remdepo-bot

# Find the most recent backup
echo "🔍 Looking for database backups..."
BACKUP_FILES=(bot.db.backup.*)
if [ ${#BACKUP_FILES[@]} -eq 0 ]; then
    echo "❌ No backup files found!"
    echo "Available files:"
    ls -la bot.db*
    exit 1
fi

# Sort by modification time and get the newest
LATEST_BACKUP=$(ls -t bot.db.backup.* | head -1)
echo "📁 Latest backup: $LATEST_BACKUP"

# Show backup info
echo "📊 Backup info:"
ls -lh "$LATEST_BACKUP"
echo "📅 Created: $(stat -c %y "$LATEST_BACKUP")"

# Confirm restore
echo ""
echo "⚠️  WARNING: This will overwrite your current database!"
echo "Current database:"
ls -lh bot.db 2>/dev/null || echo "No current database found"
echo ""
read -p "Are you sure you want to restore from $LATEST_BACKUP? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Restore cancelled"
    exit 1
fi

# Create a backup of current database before restore
if [ -f "bot.db" ]; then
    CURRENT_BACKUP="bot.db.emergency_backup.$(date +%Y%m%d_%H%M%S)"
    echo "💾 Backing up current database as: $CURRENT_BACKUP"
    cp bot.db "$CURRENT_BACKUP"
fi

# Restore from backup
echo "🔄 Restoring database..."
cp "$LATEST_BACKUP" bot.db

# Verify restore
echo "🔍 Verifying database..."
if python3 -c "
import sqlite3
try:
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    user_count = cursor.fetchone()[0]
    print(f'✅ Database restored: {user_count} users found')
    conn.close()
except Exception as e:
    print(f'❌ Database error: {e}')
    exit(1)
"; then
    echo "✅ Database restored successfully!"
else
    echo "❌ Database restore failed!"
    exit 1
fi

# Start the bot
echo "▶️ Starting bot..."
sudo systemctl start remdepo-bot

# Check if bot started
sleep 3
if sudo systemctl is-active --quiet remdepo-bot; then
    echo "✅ Bot started successfully!"
    echo "📊 Bot status:"
    sudo systemctl status remdepo-bot --no-pager
else
    echo "❌ Bot failed to start!"
    echo "📋 Check logs:"
    sudo journalctl -u remdepo-bot -n 20
    exit 1
fi

echo ""
echo "🎉 EMERGENCY RESTORE COMPLETED!"
echo "================================"
echo "✅ Database restored from: $LATEST_BACKUP"
echo "✅ Bot is running"
echo "📊 Check status: sudo systemctl status remdepo-bot"
echo "📋 Check logs: sudo journalctl -u remdepo-bot -f"
