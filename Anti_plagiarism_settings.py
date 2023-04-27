# Глобальные настройки выгрузки
DOMAIN = 'https://contest.yandex.ru'
CUSTOM_COOKIE = {
    "Session_id": ...
}
IS_USES_MULTIPROCESSING = True
PROCESSOR_COUNT = 24

# Настройки выгружаемого контеста
CONTEST_ID = ...
IGNORE_PROBLEMS_LIST = ['Обратная польская запись', 'Простая очередь']

# Настройки пользователей
USERS_LOGINS_FILE = 'students.csv'  # В csv должны быть колонки 'login', 'fio'
IS_REMOVE_OTHER_USERS = True
DEFAULT_NAME_FOR_OTHER_USERS = 'Преподаватель'

# Настройки предварительной проверки всех новых решений на контесте
IS_START_SEARCH_IN_CONTEST = True
BASIC_TIME_DELAY_SEC = 80
TIME_BETWEEN_CONTEST_CHECKS = 10

# Настройки Гугл таблиц
CREDENTIALS_FILE = 'credentials.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
spreadsheet_id = ...
LIST_NAME = 'Антиплагиат'
sheetId = ...
