import pytest

from pydeckard import config
from pydeckard import replies


@pytest.fixture()
def always_reply():
    """Force bot to always reply, so we can test its replies reliably.
    """
    old_value = config.VERBOSITY
    config.VERBOSITY = 1.0
    yield
    config.VERBOSITY = old_value



PYTHON_MESSAGES = [
    'Necesito ayuda con python, gracias',
    'Este es el grupo de piton Canarias',
    'Creo que pitón esta mal escrito'
]


@pytest.mark.parametrize('python_message', PYTHON_MESSAGES)
def test_reply_with_python(always_reply, python_message):
    reply = replies.triggers_reply(python_message)
    assert reply in replies.THE_ZEN_OF_PYTHON


def test_long_answer(always_reply):
    message = 'He visto cosas'
    reply = replies.triggers_reply(message)
    assert 'Es hora de morir' in reply
    assert 'Tannhäuser' in reply


def test_java_reply(always_reply):
    message = 'Yo antes programaba java pero ya no'
    reply = replies.triggers_reply(message)
    assert 'BIBA JABA' in reply


def test_princesa_prometida_reply(always_reply):
    expected = (
        "Hola, soy Iñigo Montoya. Tú mataste a mi padre. Prepárate a"
        "morir."
        )
    message = 'La Princesa Prometida es un peliculón'
    assert replies.triggers_reply(message) == expected


def test_inconcebible_reply(always_reply):
    expected = (
        "Siempre usas esa palabra y no creo que signifique"
        " lo que tú crees que significa."
        )
    message = 'Eso que me dices es inconcebible!'
    assert replies.triggers_reply(message) == expected


def test_repliest_consistent_data_structures():
    for tupla in replies.REPLIES:
        assert len(tupla) == 2
        keywords, options = tupla
        assert isinstance(keywords, set)
        assert isinstance(options, list)


