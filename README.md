# cryptoBot

A simple telegram bot for notifications about changes in cryptocurrency rates.

Installation:
1) Create a virtual python environment and install dependencies from the requirements.txt file
2) Change the settings.json file: set your Telegram token and chat id, add or remove currency pairs, specify the price change threshold at which the bot will send notifications and the frequency of price updates
3) Create a new system unit from the cryptoBot.service file and activate it

Every time the price of a currency differs from the last remembered value by more than a threshold value, the bot will send a notification and remember new price.
