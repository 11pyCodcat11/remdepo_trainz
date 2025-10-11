#!/bin/bash

# 🔄 Manual Bot Restart Script
# Use this to manually restart the bot on the server

echo "🔄 Manual Bot Restart"
echo "===================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root: sudo $0"
    exit 1
fi

# Stop the bot
echo "⏹️ Stopping bot..."
systemctl stop remdepo-bot || true
sleep 3

# Force kill any remaining processes
echo "🔪 Force killing any remaining bot processes..."
pkill -f "python.*bot.main" || true
sleep 2

# Start the bot
echo "▶️ Starting bot..."
systemctl start remdepo-bot

# Wait and check status
sleep 5
if systemctl is-active --quiet remdepo-bot; then
    echo "✅ Bot restarted successfully!"
    echo "📊 Bot status:"
    systemctl status remdepo-bot --no-pager
    
    # Check if process is actually running
    if pgrep -f "python.*bot.main" > /dev/null; then
        echo "✅ Bot process is running!"
    else
        echo "⚠️ Bot process not found"
    fi
else
    echo "❌ Bot failed to start!"
    echo "📋 Check logs:"
    journalctl -u remdepo-bot -n 10
    exit 1
fi

echo ""
echo "🎉 Bot restart completed!"
echo "📊 Monitor logs: journalctl -u remdepo-bot -f"
