from telebot import TeleBot
import os
from dotenv import load_dotenv
from pprint import pprint
from datetime import datetime, timedelta, time
import requests
import exceptions as err
import logging
import time

load_dotenv()
# Здесь задана глобальная конфигурация для всех логгеров:
logging.basicConfig(
    level=logging.DEBUG,
    filename='program.log',
    filemode='w',
    format='(%(filename)s -> %(funcName)s -> %(lineno)s) %(asctime)s, %(name)s: %(levelname)s - %(message)s'
)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверка переменых окружения."""
    if PRACTICUM_TOKEN is None:
        logging.critical('Не указан токен практикума')
        raise err.NoEnvironmentVariable('Не указан токен практикума')
    elif TELEGRAM_TOKEN is None:
        raise err.NoEnvironmentVariable('Не указан токен телеграм бота')
    elif TELEGRAM_CHAT_ID is None:
        raise err.NoEnvironmentVariable('Не указан ваш id')


def send_message(bot, message):
    """Ответ бота."""
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)


def get_api_answer(timestamp):
    """Ображение к API практикума."""
    payload = {'from_date': timestamp}
    try:
        homework_statuses = requests.get(ENDPOINT, headers=HEADERS, params=payload)
        result = homework_statuses.json()
        return check_response(result.get('homeworks'))
    except Exception as error:
        logging.error(f'Ошибка API: {error}')
        print(f'Ошибка подключения к API {error}')


def check_response(response):
    print(111)
    print(response)
    # return response.get('homeworks')
    # if response is not None:
    #     print('ничего нет')


def parse_status(homework):
    homework_name = homework.get('homework_name')
    verdict = HOMEWORK_VERDICTS[homework.get('status')]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    # Создаем объект класса бота
    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int((datetime.now() - timedelta(days=20)).timestamp())
    check_tokens()
    # print(get_api_answer(timestamp))
    # print(parse_status(get_api_answer(timestamp)[0]))
    # send_message(bot, parse_status(get_api_answer(timestamp)[0]))
    while True:
        try:
            result = get_api_answer(timestamp)
            time.sleep(1)
            if result == get_api_answer(timestamp):
                send_message(bot,)
                print(parse_status(result[0]))

        except Exception as error:
            message = f'Сбой в работе программы: {error}'


if __name__ == '__main__':
    main()
