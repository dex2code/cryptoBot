from loguru import logger
from time import sleep

import sys, requests, json


@logger.catch
def send_tg_messages(message: str="") -> None:
    for tg_account in app_settings['TG_ACCOUNTS']:
        for tg_chat in tg_account['TG_CHATS']:
            try:
                tg_answer = requests.post(url=f"https://api.telegram.org/bot{tg_account['TG_TOKEN']}/sendMessage", data={'chat_id': tg_chat, 'text': f"{tg_account['TG_NICK']}{message}"})
            except Exception as E:
                logger.warning(f"Cannot send TG message to chat id {tg_chat}: ({str(E)})")

            if tg_answer.status_code != 200:
                logger.warning(f"Cannot send TG message to chat id {tg_chat}: HTTP {tg_answer.status_code}")
            else:
                logger.info(f"TG message sent to chat id {tg_chat}")


@logger.catch
def main() -> None:
    logger.info(f"entering main loop...")

    while True:
        logger.info(f"sleeping for {app_settings['PAUSE_IN_SECONDS']} seconds...")
        sleep(app_settings['PAUSE_IN_SECONDS'])

        logger.info(f"requesting {app_settings['API_ENDPOINT']}{tickers_text}")
        try:
            api_response = requests.get(f"{app_settings['API_ENDPOINT']}{tickers_text}")
        except Exception as E:
            logger.warning(f"cannot request API endpoint: ({str(E)})")
            send_tg_messages(message=f"🚨 API exception: ({str(E)})")
            continue

        if api_response.status_code != 200:
            logger.warning(f"API Error: HTTP {api_response.status_code}")
            send_tg_messages(message=f"🚨 API Error: HTTP {api_response.status_code}")
            continue

        try:
            api_response_json = api_response.json()
        except Exception as E:
            logger.error(f"cannot decode API JSON: ({str(E)})")
            send_tg_messages(message=f"🚨 API JSON error: ({str(E)})")
            continue

        logger.info(f"received API answer: {api_response_json}")

        for api_ticker in api_response_json:
            try:
                api_ticker_symbol = str(api_ticker['symbol'])
                api_ticker_price = int(float(api_ticker['price']))
            except Exception as E:
                logger.error(f"cannot operate API JSON: ({str(E)})")
                send_tg_messages(message=f"🚨 API JSON error: ({str(E)})")
                continue

            diff_ticker = api_ticker_price - op_ticker[api_ticker_symbol]
            if abs(diff_ticker) > app_settings['TICKERS'][api_ticker_symbol]:
                logger.info(f"{api_ticker_symbol} overheads treshold {app_settings['TICKERS'][api_ticker_symbol]} with price ({op_ticker[api_ticker_symbol]} -> {api_ticker_price})")

                if diff_ticker > 0:
                    msg_text = f"🟢 {api_ticker_symbol}: ${op_ticker[api_ticker_symbol]:,} -> ${api_ticker_price:,}"
                else:
                    msg_text = f"🔴 {api_ticker_symbol}: ${op_ticker[api_ticker_symbol]:,} -> ${api_ticker_price:,}"
                
                op_ticker[api_ticker_symbol] = api_ticker_price
                send_tg_messages(message=msg_text)
            else:
                logger.info(f"no {api_ticker_symbol} treshold overhead ({op_ticker[api_ticker_symbol]} -> {api_ticker_price})")


if __name__ == "__main__":
    logger.add("main.log", format="{time} -- {level} -- {message}", level="INFO", rotation="1 week", compression="zip")
    logger.info(f"Crypto Telegram Bot starting service...")

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

    send_tg_messages(message=f"✅ Started to watch the following currencies: {tickers_list}")

    sys.exit(main())
