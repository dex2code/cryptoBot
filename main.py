from loguru import logger
from dotenv import load_dotenv
from time import sleep

import requests
import json
import os, sys


@logger.catch
def main():
    try:
        load_dotenv(dotenv_path=".env")
    except Exception as E:
        logger.error(f"Cannot read .env file: '{str(E)}'")
        sys.exit()

    try:
        TG_TOKEN = os.getenv(key="TG_TOKEN")
        TG_CHAT = json.loads(os.getenv(key="TG_CHAT"))
    except Exception as E:
        logger.error(f"Cannot get env key: '{str(E)}'")
        sys.exit()
    logger.info(f".env loaded successfully")


    with open("settings.json", "r") as s:
        app_settings = json.load(s)
    logger.info(f"app settings loaded successfully")
    logger.info(f"using {app_settings['API_ENDPOINT']} as API Endpoint")
    logger.info(f"setting pause {app_settings['PAUSE_IN_SECONDS']} seconds between requests")


    tickers_list = []
    op_ticker = {}
    for currency in app_settings['TICKERS']:
        tickers_list.append(currency)
        op_ticker[currency] = 0
    tickers_text = str(tickers_list).upper().replace("'", "\"").replace(" ", "")
    logger.info(f"setting tickers for API request: {tickers_text}")
    logger.info(f"setting op_tickers: {op_ticker}")


    logger.info(f"entering main loop...")
    while True:
        logger.info(f"sleeping for {app_settings['PAUSE_IN_SECONDS']} seconds...")
        sleep(app_settings['PAUSE_IN_SECONDS'])

        logger.info(f"requesting {app_settings['API_ENDPOINT']}{tickers_text}")
        try:
            api_response = requests.get(f"{app_settings['API_ENDPOINT']}{tickers_text}")
            if api_response.status_code != 200:
                logger.error(f"API Error: {api_response.status_code}")
                requests.post(url=f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", data={'chat_id': TG_CHAT, 'text': f" 🚨 API Error: {api_response.status_code}"})
                continue
        except Exception as E:
            logger.error(f"cannot request API endpoint: '{str(E)}'")
            requests.post(url=f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", data={'chat_id': TG_CHAT, 'text': f" 🚨 API exception: ({str(E)})"})
            continue

        try:
            api_response_json = api_response.json()
        except Exception as E:
            logger.error(f"cannot decode API JSON: '{str(E)}'")
            requests.post(url=f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", data={'chat_id': TG_CHAT, 'text': f" 🚨 API JSON error: ({str(E)})"})
            continue

        logger.info(f"received API answer: {api_response_json}")

        for api_ticker in api_response_json:
            try:
                api_ticker_symbol = str(api_ticker['symbol'])
                api_ticker_price = int(float(api_ticker['price']))
            except Exception as E:
                logger.error(f"cannot operate API JSON: '{str(E)}'")
                requests.post(url=f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", data={'chat_id': TG_CHAT, 'text': f" 🚨 API JSON error: ({str(E)})"})
                continue

            diff_ticker = api_ticker_price - op_ticker[api_ticker_symbol]
            if abs(diff_ticker) > app_settings['TICKERS'][api_ticker_symbol]:
                logger.info(f"{api_ticker_symbol} overhead treshold {app_settings['TICKERS'][api_ticker_symbol]} with price {api_ticker_price}")
                if diff_ticker > 0:
                    msg_text = f" 🟩 {api_ticker_symbol}: ${api_ticker_price:,}"
                else:
                    msg_text = f" 🟥 {api_ticker_symbol}: ${api_ticker_price:,}"
                
                try:
                    tg_response = requests.post(url=f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", data={'chat_id': TG_CHAT, 'text': msg_text})
                except Exception as E:
                    logger.warning(f"cannot send TG message: ({str(E)})")
                
                if tg_response.status_code == 200:
                    op_ticker[api_ticker_symbol] = api_ticker_price
                    logger.info(f"sent TG message for {api_ticker_symbol}")
                else:
                    logger.warning(f"cannot send TG message: ({tg_response.status_code}")
            else:
                logger.info(f"no {api_ticker_symbol} treshold overhead ({op_ticker[api_ticker_symbol]} -> {api_ticker_price})")


if __name__ == "__main__":
    logger.add("main.log", format="{time} -- {level} -- {message}", level="INFO", rotation="1 week", compression="zip")
    logger.info(f"Crypto Telegram Bot starting service...")
    sys.exit(main())
