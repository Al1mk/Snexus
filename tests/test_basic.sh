#!/bin/bash

# Simple test script for Snexus Bot
# This script tests basic functionality of the bot

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python3 is not installed. Please install Python 3.10 or higher."
    exit 1
fi

# Check if required modules are installed
python3 -c "import telegram" &> /dev/null
if [ $? -ne 0 ]; then
    echo "Python-telegram-bot is not installed. Please run: pip install -r requirements.txt"
    exit 1
fi

# Check if config file exists
if [ ! -f "config/.env" ]; then
    echo "Config file not found. Please create config/.env file."
    exit 1
fi

# Check database connection
echo "Testing database connection..."
python3 -c "
import sys
sys.path.append('.')
from database.db import Database
db = Database()
connection = db.get_connection()
if connection:
    print('Database connection successful')
    connection.close()
else:
    print('Database connection failed')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "Database connection test failed."
    exit 1
fi

echo "All tests passed successfully!"
exit 0
