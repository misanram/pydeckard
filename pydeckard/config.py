from typing import NamedTuple, Any, List

from prettyconf import config as _config


_config_registry: List = []


class _ConfigItem(NamedTuple):
    name: str
    value: Any
    suppress_log: bool = False

    def log_value(self, logger_method, indent=False):
        if indent:
            _msg = '    %s = %s'
        else:
            _msg = '%s = %s'
        value = "***PRIVATE***" if self.suppress_log else self.value
        logger_method(_msg, self.name, value)


def config(item: str, cast=lambda v: v, suppress_log=False, **kwargs):
    value = _config(item, cast, **kwargs)
    _config_registry.append(_ConfigItem(item, value, suppress_log))
    return value


def log_bot_configuration(logger_method):
    logger_method("Bot configuration:")
    for config_item in _config_registry:
        config_item.log_value(logger_method, indent=True)


DEBUG = config('DEBUG', cast=_config.boolean, default=False)

TELEGRAM_BOT_TOKEN = config(
    "TELEGRAM_BOT_TOKEN",
    default="put here the token of your bot",
    suppress_log=True,
    )

# How likely is the bot to be triggered by one of the patterns
# it recognises.
# Allowed values: A float from 0 to 1 (0.0 will disable all bot
# replies, 1.0 makes the bot to reply always). Default value
# of 0.33 makes one reply every third message, on
# average.
VERBOSITY = config("BOT_VERBOSITY", float, default=0.33)


# Log level, default is WARNING
LOG_LEVEL = config('LOG_LEVEL', default='WARNING')

# Poll interval for telegram API request, default is 3 seconds
POLL_INTERVAL = config('POLL_INTERVAL', int, default=3)

# Bot message for start command
BOT_GREETING = config(
    'BOT_GREETING',
    default=(
        "<b>Hi!</b> I'm a friendly, <s>crazy</s>"
        " slightly psychopath robot"
        ),
    )

# A username longer than this will be considered non-human
# - Allowed values: An integer larger than 1
MAX_HUMAN_USERNAME_LENGTH = config(
    'MAX_HUMAN_USERNAME_LENGTH',
    cast=int,
    default=100,
    )


# We have found, through empiric evidence, that a large
# ratio of Chinese characters usually indicates the user
# is a spammer or bot. This sets the maximum allowed
# percent of Chinese characters before considering the
# user a bot.
# - Allowed values: A float from 0 to 1
MAX_CHINESE_CHARS_PERCENT = config(
    'MAX_CHINESE_CHARS_PERCENT',
    cast=float,
    default=0.15,
    )


# Delay (in seconds) to wait before sending welcome message. New users have
# 5 minutes to solve a captcha. The default delay is 5 and a half minutes.
WELCOME_DELAY = config('WELCOME_DELAY', int, default=330)


def bot_replies_enabled() -> bool:
    return VERBOSITY > 0


MAXLEN_FOR_USERNAME_TO_TREAT_AS_HUMAN = 100

CHINESE_CHARS_MAX_PERCENT = 0.15
