# Snexus Telegram Bot - Documentation

## Overview
This document provides information about the Snexus Telegram Bot, the changes made to fix issues, and instructions for maintenance and future development.

## Issues Fixed
1. **Button Functionality**: Fixed inconsistencies between bot.py and main.py that were causing button functionality issues
2. **Menu Functions**: Properly implemented all menu functions to ensure correct navigation
3. **Callback Handler**: Created a unified callback handler implementation
4. **Environment Setup**: Created proper .env file with configuration for API credentials
5. **Database Setup**: Ensured proper database setup and connection

## Project Structure
- **bot_unified.py**: The main bot file that combines functionality from both bot.py and main.py
- **config/**: Contains configuration files including config.py
- **database/**: Contains database-related files including db.py and setup_db.py
- **handlers/**: Contains handler functions for different commands and features
- **models/**: Contains database models for different entities
- **services/**: Contains service functions for external APIs
- **utils/**: Contains utility functions
- **.env**: Contains environment variables and API credentials

## Setup Instructions
1. Clone the repository:
   ```
   git clone https://github.com/Al1mk/Snexus.git
   ```

2. Install dependencies:
   ```
   pip3 install -r requirements.txt
   ```

3. Create a .env file with the following content:
   ```
   # Telegram Bot Configuration
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   ADMIN_USER_IDS=your_admin_user_id

   # Database Configuration
   DB_HOST=localhost
   DB_USER=snexus_user
   DB_PASSWORD=your_db_password
   DB_NAME=snexus_db

   # Download Limits
   DAILY_DOWNLOAD_LIMIT_MB=2048  # 2GB in MB

   # VIP Subscription Prices (in Toman)
   ONE_MONTH_PRICE=50000
   THREE_MONTH_PRICE=140000

   # Payment Information
   PAYMENT_CARD_NUMBER=
   PAYMENT_CARD_OWNER=

   # Spotify API Credentials
   SPOTIFY_CLIENT_ID=your_spotify_client_id
   SPOTIFY_CLIENT_SECRET=your_spotify_client_secret

   # YouTube API Key (Optional)
   YOUTUBE_API_KEY=your_youtube_api_key

   # Logging Configuration
   LOG_LEVEL=INFO
   ```

4. Set up the MySQL database:
   ```
   sudo mysql -e "CREATE DATABASE IF NOT EXISTS snexus_db; CREATE USER IF NOT EXISTS 'snexus_user'@'localhost' IDENTIFIED BY 'your_db_password'; GRANT ALL PRIVILEGES ON snexus_db.* TO 'snexus_user'@'localhost'; FLUSH PRIVILEGES;"
   ```

5. Initialize the database:
   ```
   python3 database/setup_db.py
   ```

6. Run the bot:
   ```
   python3 bot_unified.py
   ```

## API Credentials
The bot requires API credentials for the following services:

1. **Spotify API**:
   - Register at [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)
   - Create a new application
   - Use http://localhost:8888/callback as the Redirect URI
   - Get the Client ID and Client Secret

2. **YouTube API**:
   - Register at [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable the YouTube Data API v3
   - Create API credentials and get the API Key

## Running as a Service
To run the bot as a service that starts automatically on system boot:

1. Create a systemd service file:
   ```
   sudo nano /etc/systemd/system/snexus-bot.service
   ```

2. Add the following content:
   ```
   [Unit]
   Description=Snexus Telegram Bot
   After=network.target

   [Service]
   User=your_username
   WorkingDirectory=/path/to/Snexus
   ExecStart=/usr/bin/python3 /path/to/Snexus/bot_unified.py
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

3. Enable and start the service:
   ```
   sudo systemctl enable snexus-bot.service
   sudo systemctl start snexus-bot.service
   ```

4. Check the status:
   ```
   sudo systemctl status snexus-bot.service
   ```

## Maintenance
1. **Logs**: Check the logs directory for error logs
2. **Database Backup**: Regularly backup the MySQL database
3. **API Credentials**: Keep API credentials up to date
4. **Dependencies**: Regularly update dependencies to ensure security and functionality

## Troubleshooting
1. **Bot Not Responding**: Check if the bot process is running and check the logs
2. **Database Connection Issues**: Verify MySQL is running and credentials are correct
3. **API Errors**: Verify API credentials are valid and not expired
4. **Button Functionality Issues**: Ensure the callback handler is properly implemented

## Future Improvements
1. **Error Handling**: Improve error handling for better user experience
2. **Caching**: Implement caching for frequently accessed data
3. **Analytics**: Add analytics to track user behavior and bot performance
4. **Multi-language Support**: Add support for multiple languages
5. **Payment Integration**: Integrate with payment gateways for VIP subscriptions
