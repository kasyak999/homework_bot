from telebot import TeleBot
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
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
    format=(
        '(%(filename)s -> %(funcName)s -> %(lineno)s)'
        '%(asctime)s, %(name)s: %(levelname)s - %(message)s'
    )
)

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
    if PRACTICUM_TOKEN is None:
        logging.critical('Не указан токен практикума')
        raise err.NoEnvironmentVariable('Не указан токен практикума')
    elif TELEGRAM_TOKEN is None:
        logging.critical('Не указан токен телеграмм')
        raise err.NoEnvironmentVariable('Не указан токен телеграм бота')
    elif TELEGRAM_CHAT_ID is None:
        logging.critical('Не указан chat_id')
        raise err.NoEnvironmentVariable('Не указан ваш id')


def send_message(bot, message):
    """Ответ бота."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.debug('Сообщение отправлено')
    except Exception as error:
        logging.error(error)


def get_api_answer(timestamp):
    """Обращение к API."""
    payload = {'from_date': timestamp}
    try:
        homework_statuses = requests.get(
            url=ENDPOINT, headers=HEADERS, params=payload
        )
    except requests.RequestException as error:
        logging.error(error)
    else:
        if homework_statuses.status_code != 200:
            error = f'Код ответа Api: {homework_statuses.status_code}'
            logging.error(error)
            raise err.NoEnvironmentVariable(error)
        return homework_statuses.json()


def check_response(response):
    """Проверяет ответ API."""
    if not isinstance(response, dict):
        error = f'Ответ сервера, не является словарем {type(response)}'
        logging.error(error)
        raise TypeError(error)
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        error = (
            f'Ответ сервера: homeworks не является списком {type(homeworks)}'
        )
        logging.error(error)
        raise TypeError(error)
    if not homeworks:
        logging.debug("Нет информации.")
    return homeworks[0]


def parse_status(homework):
    """Извлекает из информации."""
    homework_name = homework.get('homework_name')
    verdict = homework.get('status')
    if homework_name is None:
        logging.debug('Нет значения homework_name.')
        raise err.NoEnvironmentVariable(
            'Нет значения homework_name.'
        )
    elif verdict is None or verdict not in HOMEWORK_VERDICTS:
        logging.debug('Нет значения status.')
        raise err.NoEnvironmentVariable(
            'Нет значения status.'
        )
    try:
        verdict = HOMEWORK_VERDICTS[homework.get('status')]
    except KeyError:
        verdict = 'Статус не определен'
        logging.debug(verdict)
        raise err.NoEnvironmentVariable(verdict)
    finally:
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    # Создаем объект класса бота
    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int((datetime.now() - timedelta(days=2)).timestamp())
    check_tokens()
    status = None
    while True:
        try:
            answer_api = check_response(get_api_answer(timestamp))
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
        else:
            if status != answer_api.get('status'):
                send_message(bot, parse_status(answer_api))
                logging.debug('Статус изменился.')
            status = answer_api.get('status')
        finally:
            time.sleep(TIME_SLEEP)


if __name__ == '__main__':
    main()
