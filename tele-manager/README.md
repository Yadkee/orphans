# TeleManager
Telegram bot

This is the actual list of commands:
* /birthday Add or list your friend's birthdays
* /remind I can notify you in less than 24 hours
* /event Add or list your future events
* /cancel Cancels the current operation

## Requirements
* Python 3
* MySQL for Python

## Setup
1. Install the requirements
2. Have the MySQL server running
3. Make sure you have secret/config.json

### Config.json
```
/root
    /main.py
    /secret
        /config.json
```
```json
{
    "TOKEN": "Telegram-API-Token",
    "ADMIN": USER_ID,
    "USERS": [USER_ID1, USER_ID2, USER_ID3],
    "DB_ARGS": {"user": "user", "password": "pass"}
}
```