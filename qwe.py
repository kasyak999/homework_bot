import exceptions as err


try:
    qwe = 300
    if qwe != 200: # status_code
        raise err.NoEnvironmentVariable('Ошибка API: Неуспешный запрос, код ответа')
except err.NoEnvironmentVariable as error:
    # raise  # Перебрасываем кастомное исключение
    print(error)
except Exception as error:
    print(f'Ошибка подключения к API {error}')