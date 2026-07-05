#!/usr/bin/env python3

import dataclasses
import grp
import platform
import pwd
import sys
import textwrap

from datetime import datetime as DateTime

from abc import ABC, abstractmethod
from pathlib import Path
from typing import (
    List,
    Optional,
    )

from pydeckard import config
from telegram import User


GREEN = '\033[0;32m'
END = '\033[0m'
OK = f'{GREEN}[OK]{END}'

SYSTEMD_UNIT_TEMPLATE = """[Unit]
Description=PyDeckard
After=network.target

[Service]
Type=simple
User={user_name}
Group={group_name}
WorkingDirectory={project_path}
ExecStart={bot_executable}
Environment=PYTHONUNBUFFERED=1
Restart=always

[Install]
WantedBy=multi-user.target
Alias=PyDeckard.service
"""


def box(title: str, text: str, width: int = 68) -> str:
    len_title = len(title)
    header = ''.join([
        '┌',
        '─' * (width - 7 - len_title),
        '┤ ',
        title,
        ' ├─┐',
        ])
    buff = [header]
    paragraphs = text.split('\n')
    for _i, paragraph in enumerate(paragraphs):
        lines = textwrap.wrap(paragraph, width=width - 4)
        for line in lines:
            buff.append(f'│ {line.ljust(width - 4)} │')
        if _i > 0:
            buff.append(''.join(['│', ' ' * (width - 2), '│']))
    buff.append(''.join(['└', '─' * (width - 2), '┘']))
    return '\n'.join(buff)


def is_chinese(c: str) -> bool:
    """
    Detects if a character is chinese.

    Returns:

        (bool): ``True`` if the character passed as
        parameter is a Chinese one, ``False`` otherwise.
    """
    num = ord(c)
    return any([
        0x2E80 <= num <= 0x2FD5,
        0x3190 <= num <= 0x319F,
        0x3400 <= num <= 0x4DBF,
        0x4E00 <= num <= 0x9FCC,
        0x6300 <= num <= 0x77FF,
        ])


def too_much_chinese_chars(s: str, percent: float | None = None) -> bool:
    """Detects if a text contains too many chinese characters.
    """
    percent = percent or config.CHINESE_CHARS_MAX_PERCENT
    letters = list(s)
    num_chinese_chars = sum([is_chinese(c) for c in letters])
    name_percent = num_chinese_chars / len(letters)
    # More than allowed chars are Chinese
    return name_percent > percent


def is_valid_name(user: User) -> bool:
    """Check if a username is valid.
    """
    return len(user.first_name) <= config.MAX_HUMAN_USERNAME_LENGTH


def is_tgmember_sect(first_name: str):
    return "tgmember.com" in first_name.lower()


def is_bot(user: User) -> bool:
    """
    Checks if a new user is a bot.

    So far this function checks:

    - the length of the username
    - Ratio of chinese characters in name
    - tg_member

    In the future, we can add more conditions to improve
    our estimation of the user being a bot. Add all the
    checks that you consider necessary.

    Parameters:

        user (User): The new User

    Returns:

        (bool): ``True`` if the new user is considered a bot (according to
        our rules), ``False`` otherwise.
    """
    return any([
        not is_valid_name(user),
        too_much_chinese_chars(user.first_name),
        is_tgmember_sect(user.first_name),
        ])


def pluralise(number: int, singular: str, plural: Optional[str] = None) -> str:
    if plural is None:
        plural = f"{singular}s"
    return singular if number == 1 else plural


def since(reference) -> str:
    """Returns a textual description of time passed.

    Parameters:

     - reference (DateTime): the datetime used to get the difference
        as delta.

    Returns:

        (str): Text describing the time passed since the reference.
    """
    dt = DateTime.now()
    delta = dt - reference
    buff = []
    days = delta.days
    if days:
        buff.append(f"{days} {pluralise(days, 'day')}")
    seconds = delta.seconds
    if seconds > 3600:
        hours = seconds // 3600
        buff.append(f"{hours} {pluralise(hours, 'hour')}")
        seconds %= 3600
    minutes = seconds // 60
    if minutes > 0:
        buff.append(f"{minutes} {pluralise(minutes, 'minute')}")
    seconds %= 60
    buff.append(f"{seconds} {pluralise(seconds, 'second')}")
    return " ".join(buff)


@dataclasses.dataclass
class BaseParameter(ABC):
    name: str
    message: str
    acceptable: List | None = None
    start_value: int | float | None = None
    stop_value: int | float | None = None

    def _help_prompt(self) -> str:
        if self.acceptable:
            return f' [{self._acceptables_as_list()}]'
        if self.start_value is not None and self.stop_value is not None:
            return f' [{self.start_value} <= value < {self.stop_value}]'
        if self.start_value is not None and self.stop_value is None:
            return f' [{self.start_value} <= value]'
        if self.start_value is None and self.stop_value is not None:
            return f' [value < {self.start_value}]'
        return ''

    def _acceptables_as_list(self) -> str:
        if self.acceptable:
            return ', '.join([str(_) for _ in self.acceptable])
        return ''

    def _data_is_acceptable(self, data):
        '''Raises a ValueError if the data breaks some validation.

        If evertything is fine, nothing happens, but if any of the
        rules of the validation is broken, a ``ValueError``
        exception is raised.

        Paramenters:

            data (str|int|float): Value to be validated.

        Returns:

            ``None``.
        '''
        if self.acceptable and data not in self.acceptable:
            raise ValueError(
                f'El valor pasado [{data!r}] no está'
                ' en la lista de valores aceptables:'
                f' {self._acceptables_as_list()}.'
                )
        if self.start_value is not None and self.stop_value is not None:
            if data < self.start_value or data >= self.stop_value:
                raise ValueError(
                    f'El valor pasado [{data!r}] no está'
                    ' comprendido en el rango de valores aceptables:'
                    f' debería ser mayor o igual que {self.start_value}'
                    f' y estríctamente menor que {self.stop_value}.'
                    )
        if self.start_value is not None and self.stop_value is None:
            if data < self.start_value:
                raise ValueError(
                    f'El valor pasado [{data!r}] no está'
                    ' comprendido en el rango de valores aceptables:'
                    f' debería ser mayor o igual que {self.start_value}.'
                    )
        if self.start_value is None and self.stop_value is not None:
            if data >= self.stop_value:
                raise ValueError(
                    f'El valor pasado [{data!r}] no está'
                    ' comprendido en el rango de valores aceptables:'
                    ' debería ser estríctamente menor'
                    f' que {self.stop_value}.'
                    )

    def ask_value(self) -> int | float | bool | str | None:
        prompt = f'{self.message}{self._help_prompt()}: '
        while True:
            data = input(prompt).strip()
            if not data:
                return None
            try:
                return self.get_value(data)
            except ValueError as err:
                print(
                    'Error al definir el valor de {self.name}',
                    str(err),
                    'Introduzca un nuevo valor o dejelo en blanco'
                    ' para usar el valor por defecto.',
                    sep='\n',
                    )

    @abstractmethod
    def get_value(self, data) -> int | float | bool | str | None:
        pass


class IntParameter(BaseParameter):

    def get_value(self, data) -> int:
        value = int(data)
        self._data_is_acceptable(value)
        return value


class PercentParameter(BaseParameter):

    def __init__(self, *args, **kwargs):
        kwargs['start_value'] = 0
        kwargs['stop_value'] = 101
        super().__init__(*args, **kwargs)

    def get_value(self, data) -> float:
        value = int(data)
        self._data_is_acceptable(value)
        return round(value / 100.0, 3)


class StrParameter(BaseParameter):

    def get_value(self, data) -> str:
        value = str(data)
        self._data_is_acceptable(value)
        return value


PARAMETERS = [
    StrParameter(
        'TELEGRAM_BOT_TOKEN',
        'Introduzca el Token del Bot',
        ),
    StrParameter(
        'LOG_LEVEL',
        'Nivel de registro de logs',
        acceptable=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        ),
    IntParameter(
        'POLL_INTERVAL',
        'Intervalo de polling para la API de Telegram',
        start_value=1,
        stop_value=11,
        ),
    StrParameter(
        'BOT_GREETING',
        'Saludo del bot',
        ),
    IntParameter(
        'MAX_HUMAN_USERNAME_LENGTH',
        'Longitud máxima del username',
        ),
    PercentParameter(
        'MAX_CHINESE_CHARS_PERCENT',
        'Máximo porcentaje de caracteres chinos en username',
        ),
    IntParameter(
        'WELCOME_DELAY',
        'Tiempo de retardo para la bienvenida (en segundos)',
        ),
    ]


def get_project_dir():
    return Path(__file__).parent.parent


def setup_bot():
    """
    Automatic configaration Wizard.

    This wizard configure the bot and create an automatic
    startup system based on the operating system.

    It performs an input for each required configuration
    parameter. The ``PARAMETERS`` list contains all the defined
    parameters, each as a object derivated of ``BaseParameter``,
    which is a contaqiner for:

    - The Parameter name.
    - The Prompt for input.
    - An optional list of acceptable values
    - An optional start value
    - An optional stop value
    """

    project_path = get_project_dir()
    bin_path = Path(sys.executable).parent
    print(box(
        'PyDeckard Wizard',
        'Asistente de configuración para PyDeckard.'
        ' Configura el bot y crea un fichero .env para'
        ' los valores que queremos sobreescribir así'
        ' como el fichero Unit para arrancar el bot como'
        ' un demonio en sistemas Linux con SystemD.'
        ))
    env_values = {}
    print('Parámetros')
    print('Deje el valor en blanco si quiere usar el valor por defecto.')
    for parameter in PARAMETERS:
        value = parameter.ask_value()
        if value is None:
            continue
        env_values[parameter.name] = value
    print(env_values)
    if env_values:
        env_path = project_path / '.env'
        print(f'Generando fichero {env_path}', end=' .. ')
        with open(env_path, 'w') as fout:
            for key, value in env_values.items():
                fout.write(f'{key}={value!r}\n')
        print(OK)

    system_name = platform.system()
    match system_name:

        case 'Linux':
            stat_info = project_path.stat()
            user_name = pwd.getpwuid(stat_info.st_uid).pw_name
            group_name = grp.getgrgid(stat_info.st_gid).gr_name
            service_path = project_path / 'pydeckard.service'
            bot_executable = bin_path / 'pydeckard'
            print(f'Generando fichero unit {service_path}', end=' .. ')
            with open(service_path, 'w') as f:
                f.write(SYSTEMD_UNIT_TEMPLATE.format(
                    user_name=user_name,
                    project_path=project_path,
                    bot_executable=bot_executable,
                    group_name=group_name,
                    service_path=service_path,
                    ))
            print(OK)
            print(box(
                'Detectado sistema Linux',
                f'Archivo pydeckard.service creado en {project_path}.'
                ' Para configurar, activar e iniciar el service'
                ' en systemd ejecute los siguientes comandos:\n'
                f'\nsudo cp {service_path} /etc/systemd/system/'
                '\nsudo systemctl daemon-reload'
                '\nsudo systemctl enable --now pydeckard'
                ))
            sys.exit(0)
        case 'Darwin':
            print(box(
                system_name,
                'Entorno macOS detectado, configuración realizada.'
                'Pregúntele a Apple® como arrancarlo.',
                ))
            sys.exit(1)

        case 'Windows':
            print(box(
                system_name,
                'Entorno Windows detectado, configuración realizada.'
                ' Pregúntele a Microsoft® como arrancarlo.',
                ))
            sys.exit(1)

        case _:
            print(box(
                system_name,
                f'Entorno {system_name} desconocido. Usted mismo.',
                ))
