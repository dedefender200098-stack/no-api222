LICENSE_KEY = ''  # Брать ключ в боте, по кнопке "Софты"

TG_BOT_TOKEN = ''  # str ('2282282282:NzA4NTM1MDUxN8GGCiGs6T0Ik-kD2q7GmisthH_yyZvI8If84kN5VDkK')
TG_USER_ID = None  # int (22822822) or None
CHERRY_SOLVER_API_KEY = ''  # @CherryCaptcha_bot
CAPMONSTER_API_KEY = ''  # https://dash.capmonster.cloud/

SHUFFLE_WALLETS = False
PAUSE_BETWEEN_WALLETS = [10, 20]
PAUSE_BETWEEN_MODULES = [20, 40]
MAX_PARALLEL_ACCOUNTS = 50

RETRIES = 10  # Сколько раз повторять 'зафейленное' действие
PAUSE_BETWEEN_RETRIES = 5  # Пауза между повторами

FAUCET = False # Краник, для использования крана нужно минимум 50 поинтов 
BRIDGE = False # Бриджит ANKR из Sepolia в Neura
CYCLE_SWAPS = False  # ANRK -> ETH -> ANRK -> BTC -> ANKR  -> ... -> ....

COLLECT_PULSES = False
CLAIM_TASKS = False
CHAT_WITH_AGENTS = False


class CycleSwapSettings:
    token = ['ETH', 'BTC']  # Токен в пару к ANKR
    swap_percentage = [0.03, 0.07]  # 0.1 - 10%, 0.23 - 23% и т.п.
    cycles = [1, 2]  # Кол-во циклов свапов (ANKR -> ETH -> ANKR - это один цикл)


class ChatSettings:
    greet_messages = [
        "Hello",
        "Hi",
        "Hey",
        "Greetings",
        "Good to see you",
    ]
    num_messages = [15, 25]  # Суммарное кол-во сообщений
