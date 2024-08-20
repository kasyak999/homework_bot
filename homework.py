from telebot import TeleBot, apihelper
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import requests
import logging
import time
# from pprint import pprint


load_dotenv()
PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses1/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
TIME_SLEEP = 10 * 60

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}
ERROR_GLOBAL = {
    'PRACTICUM_TOKEN': (
        'Токен практикума PRACTICUM_TOKEN, не задан в файле .env'
    ),
    'TELEGRAM_TOKEN': (
        'Токен телеграм бота TELEGRAM_TOKEN, не задан в файле .env'
    ),
    'TELEGRAM_CHAT_ID': 'TELEGRAM_CHAT_ID не задан в файле .env',
    'errors': 'Не все переменные окружения заданы.',
    'ok': 'Все переменные окружения присутствуют в файле .env'
}
BOT_MESSAGE = {
    'error': 'ошибка телграм бота\n{error}',
    'ok': 'Сообщение отправлено',
}


def check_tokens():
    """Проверка переменых окружения."""
    errors = []
    if not globals()['PRACTICUM_TOKEN']:
        errors.append(ERROR_GLOBAL['PRACTICUM_TOKEN'])
    if not globals()['TELEGRAM_TOKEN']:
        errors.append(ERROR_GLOBAL['TELEGRAM_TOKEN'])
    if not globals()['TELEGRAM_CHAT_ID']:
        errors.append(ERROR_GLOBAL['TELEGRAM_CHAT_ID'])

    if errors:
        for error in errors:
            logging.critical(error)
        raise ValueError(ERROR_GLOBAL['errors'])
    logging.debug(ERROR_GLOBAL['ok'])


def send_message(bot, message):
    """Ответ бота."""
    try:
        bot.send_message(chat_id=globals()['TELEGRAM_CHAT_ID'], text=message)
        logging.debug(BOT_MESSAGE['ok'])
    except apihelper.ApiTelegramException as error:
        raise UserWarning(BOT_MESSAGE['error'].format(error=error)) from error


def get_api_answer(timestamp):
    """Обращение к API."""
    payload = {'from_date': timestamp}
    try:
        homework_statuses = requests.get(
            url=ENDPOINT, headers=HEADERS,
            params=payload
        )
        if homework_statuses.status_code != 200:
            raise requests.exceptions.HTTPError(
                f'код ответа Api {homework_statuses.status_code}'
            )
        return homework_statuses.json()
    except requests.RequestException as error:
        message = f''' Ошибка при запросе к API
            url={ENDPOINT}, headers={HEADERS}, params={payload}.
            {error}'''
        raise RuntimeWarning(message) from error


def check_response(response):
    """Проверяет ответ API."""
    # pprint(response)
    if not isinstance(response, dict):
        raise TypeError(
            f'ответ сервера, не является словарем {type(response)}'
        )
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        raise TypeError(
            f'ответ сервера, homeworks не является списком {type(homeworks)}'
        )
    if not homeworks:
        raise TypeError('в ответе сервера нет информации.')
    return homeworks[0]


def parse_status(homework):
    """Извлекает из информации."""
    try:
        homework_name = homework.get('homework_name')
        if not homework.get('homework_name'):
            raise ValueError(
                'в ответе сервера нет значения homework_name.'
            )
        verdict = HOMEWORK_VERDICTS[homework.get('status')]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    except KeyError:
        raise KeyError('Статус не определен')


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
                logging.debug('Статус изменился.')
            status = answer_api.get('status')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
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
        filename='program.log',
        filemode='w',
        format=(
            '(%(filename)s -> %(funcName)s -> %(lineno)s)'
            '%(asctime)s, %(name)s: %(levelname)s - %(message)s'
        )
    )
    main()
