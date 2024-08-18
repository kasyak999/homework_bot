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
    if not globals()['PRACTICUM_TOKEN']:
        mistake = 'Токен практикума не задан в файле .env'
        logging.critical(mistake)
        raise ValueError(mistake)
    elif not globals()['TELEGRAM_TOKEN']:
        mistake = 'Токен телеграм бота не задан в файле .env'
        logging.critical(mistake)
        raise ValueError(mistake)
    elif not globals()['TELEGRAM_CHAT_ID']:
        mistake = 'chat_id не задан в файле .env'
        logging.critical(mistake)
        raise ValueError(mistake)


def send_message(bot, message):
    """Ответ бота."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except apihelper.ApiTelegramException:
        raise
    else:
        logging.debug('Сообщение отправлено')


def get_api_answer(timestamp):
    """Обращение к API."""
    payload = {'from_date': timestamp}
    try:
        homework_statuses = requests.get(
            url=globals()['ENDPOINT'], headers=globals()['HEADERS'],
            params=payload
        )
        if homework_statuses.status_code != 200:
            raise requests.exceptions.HTTPError(
                f'код ответа Api {homework_statuses.status_code}'
            )
    except requests.RequestException as error:
        message = f''' Ошибка при запросе к API
            url={globals()['ENDPOINT']},
            headers={globals()['HEADERS']},
            params={payload}.
            {error}'''
        raise Exception(message) from error
    else:
        return homework_statuses.json()


def check_response(response):
    """Проверяет ответ API."""
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
        verdict = globals()['HOMEWORK_VERDICTS'][homework.get('status')]
    except KeyError:
        raise KeyError('Статус не определен')
    else:
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    # Создаем объект класса бота
    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int((datetime.now() - timedelta(days=2)).timestamp())
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
