import logging
import datetime

today = datetime.datetime.today().date()

logfile = f"./logs/telegram_bots_{today}.log"

logging.basicConfig(
    level=logging.INFO,
    filename=logfile,
    datefmt='%H:%M:%S',
    filemode="a",
    # format="%(asctime)s %(levelname)s %(message)s",
    format="%(asctime)s - %(name)-12s: %(levelname)-8s %(message)s",
)
# определить обработчик, который записывает сообщения INFO или выше в sys.stderr
console = logging.StreamHandler()
console.setLevel(logging.INFO)
# установить формат, который проще для использования консоли
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
# сказать обработчику использовать этот формат
console.setFormatter(formatter)
# добавить обработчик в корневой логгер
logging.getLogger('').addHandler(console)

# Теперь мы можем логировать в корневой логгер или любой другой логгер. Сначала корневой ...
logging.info('Start logging recording')


def record(level: str, message: str, module_name: str):
    logger = logging.getLogger(module_name)
    if level == "info":
        logger.info(message)
    elif level == "debug":
        logger.debug(message)
    elif level == "error":
        logger.error(message)
    elif level == "warn":
        logger.warning(message)
    return
