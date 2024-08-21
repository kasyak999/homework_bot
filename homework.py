from telebot import TeleBot, apihelper
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import requests
import logging
import time
import sys
# from pprint import pprint
from http import HTTPStatus
from json import JSONDecodeError
from message import MESSAGE

#
load_dotenv()
PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
TIME_SLEEP = 10 * 60

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверка переменых окружения."""
    errors = []
    if not globals()['PRACTICUM_TOKEN']:
        errors.append(MESSAGE['error_global'])
    if not globals()['TELEGRAM_TOKEN']:
        errors.append(MESSAGE['error_global1'])
    if not globals()['TELEGRAM_CHAT_ID']:
        errors.append(MESSAGE['error_global2'])

    if errors:
        for error in errors:
            logging.critical(error)
        raise ValueError(MESSAGE['error_global3'])
    logging.debug(MESSAGE['error_global_ok'])


def send_message(bot, message):
    """Ответ бота."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.debug(MESSAGE['bot_ok'])
    except apihelper.ApiTelegramException as error:
        raise ConnectionError(MESSAGE['bot_error'].format(error)) from error


def get_api_answer(timestamp):
    """Обращение к API."""
    payload = {'from_date': timestamp}
    try:
        homework_statuses = requests.get(
            url=ENDPOINT, headers=HEADERS, params=payload
        )
    except JSONDecodeError as error:
        raise ConnectionRefusedError(
            MESSAGE['json_error'].format(error)
        ) from error
    except requests.RequestException as error:
        message = MESSAGE['api_error1'].format(
            ENDPOINT, HEADERS, payload, error
        )
        raise ConnectionError(message) from error

    if homework_statuses.status_code != HTTPStatus.OK:
        raise ConnectionError(
            MESSAGE['api_error'].format(homework_statuses.status_code)
        )
    return homework_statuses.json()


def check_response(response):
    """Проверяет ответ API."""
    if not isinstance(response, dict):
        raise TypeError(MESSAGE['no_dict'].format(type(response)))
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        raise TypeError(MESSAGE['no_list'].format(type(homeworks)))
    if not homeworks:
        raise TypeError(MESSAGE['no_info'])
    return homeworks[0]


def parse_status(homework):
    """Извлекает из информации."""
    try:
        homework_name = homework.get('homework_name')
        if not homework.get('homework_name'):
            raise ValueError(MESSAGE['api_error2'])
        verdict = HOMEWORK_VERDICTS[homework.get('status')]
        return MESSAGE['status_message'].format(homework_name, verdict)
    except KeyError:
        raise KeyError(MESSAGE['not_status'])


def main():
    """Основная логика работы бота."""
    # Создаем объект класса бота
    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int((datetime.now() - timedelta(days=30)).timestamp())
    check_tokens()
    status = None
    error_shipped = None
    while True:
        try:
            answer_api = check_response(get_api_answer(timestamp))
            if status != answer_api.get('status'):
                send_message(bot, parse_status(answer_api))
                logging.debug(MESSAGE['status_changed'])
            status = answer_api.get('status')
        except Exception as error:
            message = MESSAGE['error_messages'].format(error)
            logging.error(message)
            if str(error) != str(error_shipped):
                send_message(bot, message)
            error_shipped = error
        finally:
            time.sleep(TIME_SLEEP)


if __name__ == '__main__':
    # Здесь задана глобальная конфигурация для всех логгеров:
    logging.basicConfig(
        level=logging.DEBUG,
        format=(
            '(%(filename)s -> %(funcName)s -> %(lineno)s)'
            '%(asctime)s, %(name)s: %(levelname)s - %(message)s'
        ),
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(
                filename=__file__ + '.log', mode='w', encoding='utf-8'
            ),
        ],
    )
    main()
