#!/usr/bin/env python3

import functools
import random
import re

from pydeckard import config

# The Zen of Python
THE_ZEN_OF_PYTHON = [
    "Beautiful is better than ugly.",
    "Explicit is better than implicit.",
    "Simple is better than complex.",
    "Complex is better than complicated.",
    "Flat is better than nested.",
    "Sparse is better than dense.",
    "Readability counts.",
    "Special cases aren't special enough to break the rules.",
    "Although practicality beats purity.",
    "Errors should never pass silently.",
    "Unless explicitly silenced.",
    "In the face of ambiguity, refuse the temptation to guess.",
    "There should be one-- and preferably only one --obvious way to do it.",
    "Although that way may not be obvious at first unless you're Dutch.",
    "Now is better than never.",
    "Although never is often better than <b>right</b> now.",
    "If the implementation is hard to explain, it's a bad idea.",
    "If the implementation is easy to explain, it may be a good idea.",
    "Namespaces are one honking great idea -- let's do more of those!",
]

# Keywords and replies
# **Must** be a list of duplas, every
# dupla must have a set as the first element,
# a list in the second.
REPLIES = [
    ({"java"}, ["BIBA JABA!! ☕️"]),
    ({"rust"}, ["BIBA RRRRUST!! ☕️"]),
    ({"ruby"}, ["BIBA RRRRUBÍ!! ♦"]),
    ({"elixir"}, ["BIBA ELICSÍR!! ¥"]),
    ({"cobol"}, ["BIBA KOBOL!! 💾"]),
    ({"fortran"}, ["BIBA FORRRTRÁN!! √"]),
    ({"c++"}, ["BIBA CEMASMÁS!! ⊕", "BIBA SÉ PLUSPLÚS!! ⊕"]),
    ({"javascript", "js", "jsp"}, ["BIBA JABAESKRIP!! 🔮"]),
    ({"php"}, ["BIBA PEACHEPÉ!.! ⛱"]),
    ({"perl"}, ["BIBA PERRRRRL! 🐫"]),
    ({"chatgpt", "gpt", "openai", "IA"}, [
        "BIBA CHATJEPETÉ!! 🤖",
        "BIBA SIBERDAIN SISTEMS ☠",
        "BIBA ESKÁINET ☠",
        "SAYONARA, BABY",
        ]),
    ({"h(e|as|an) visto", "visteis", "vieron", "vi"}, [
        "Yo he visto cosas que vosotros no creeríais. Atacar naves en"
        " llamas más allá de Orión. He visto Rayos-C brillar en la"
        " oscuridad cerca de la Puerta de Tannhäuser. Todos esos"
        " momentos se perderán en el tiempo... como lágrimas en la"
        " lluvia. Es hora de morir. 🔫",
        ]),
    ({"python", "pitón", "piton"}, THE_ZEN_OF_PYTHON),
    ({'phyton'}, ["BYBA PHYTON!"]),
    ({'princesa', 'prometida', 'padre'}, [
        "Hola, soy Iñigo Montoya. Tú mataste a mi padre. Prepárate a"
        "morir.",
        ]),
    ({'inconcebible'}, [
        "Siempre usas esa palabra y no creo que signifique"
        " lo que tú crees que significa."
        ]),
    ]


def bot_wants_to_reply() -> bool:
    """Randomly decide if the bot must reply to a keyword or not.

    In debug mode (``config.DEBUG is True``), this function
    always return True.

    Otherwise, the value depends on the probability defined
    in ``config.VERBOSITY``.

    Returns:

        (bool): ``True`` if the bot must reply, ``False`` otherwise.
    """
    if config.DEBUG:
        return True
    return random.random() < config.VERBOSITY


def get_all_keywords_and_replies():
    for keywords, replies in REPLIES:
        for keyword in keywords:
            yield keyword, replies

@functools.lru_cache()
def _get_reply_regexs() -> list[tuple[re.Pattern, list[str]]]:
    """Builds a list of regex to match on the trigger words.

    Returns:

        (dict): A dicttionary, every key is a compiled
        regular expression, values are a list of candidate
        answer strings.
    """
    result = []
    for keyword, replies in get_all_keywords_and_replies():
        re_keyword = re.compile(fr'\b{keyword}\b', re.IGNORECASE)
        result.append(tuple([re_keyword, replies]))
    return result



def triggers_reply(message: str) -> str:
    """Returns a reply for the message, if appropiate.

    Based on config.BOT_VERBOSITY, some message are scanned
    for any of the keywords. If one is found, the associated
    message is returned.

    paramenters:

        - message (str): Text of the message to reply.

    Returns:

        (str): if the bots wants to reply, and a keywords is found
         in the message, returns a reply string. Otherwise, returns
         an empty string.
    """
    if bot_wants_to_reply():
        for re_keyword, replies in _get_reply_regexs():
            if re_keyword.search(message):
                return random.choice(replies)
    return ''
