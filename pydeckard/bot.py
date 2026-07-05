#!/usr/bin/enb python3

from datetime import datetime as DateTime
import argparse
import logging
import logging.handlers
import pathlib
import sys
import time
from logging.handlers import RotatingFileHandler

import tomllib
import telegram
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    filters,
    MessageHandler,
    )
from telegram.constants import ParseMode

from pydeckard import config
from pydeckard import utils
from pydeckard import replies


class DeckardBot():

    def __init__(self):
        self.get_options()
        self.set_logger()
        self.started_at = DateTime.now()

    def get_options(self):
        parser = argparse.ArgumentParser(
            prog='bot',
            description='PyDeckard Bot',
            epilog='',
            )
        parser.add_argument(
            '--setup',
            action='store_true',
            help='Start the setup wizard',
            )
        with open('pyproject.toml', 'rb') as fp:
            conf = tomllib.load(fp)
            self.version = conf['project']['version']

        args = parser.parse_args()
        if args.setup:
            utils.setup_bot()

    def set_logger(self):
        self.logger = logging.getLogger('pydeckard')
        if config.DEBUG:
            log_handler = logging.StreamHandler()
        else:
            logs_dir = pathlib.Path('logs')
            if not logs_dir.exists():
                logs_dir.mkdir()
            log_handler = RotatingFileHandler(
                logs_dir / 'pydeckard.log',
                maxBytes=8*1024*1024,
                backupCount=9,
                )
        logging.basicConfig(
            level=logging.WARNING,  # Pone todos los logger a WARNING
            format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
            handlers=[log_handler],
            force=True,
            )
        # Ajustamos el nivel del logger bot
        self.logger.setLevel(config.LOG_LEVEL)
        config.log_bot_configuration(self.logger.info)

    def trace(self, msg, *args):
        self.logger.info(msg, *args)

    async def command_status(
            self,
            update: Update,
            context: ContextTypes.DEFAULT_TYPE,
            ):
        self.trace('Received command: /status')
        python_version = sys.version.split(maxsplit=1)[0]
        text = '\n'.join([
            config.BOT_GREETING,
            '- Status is <b>OK</b>',
            f'- Running since {utils.since(self.started_at)}',
            f'- Python version is {python_version}',
            ])
        if update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=text,
                parse_mode=ParseMode.HTML,
                )
            self.trace(text)

    async def command_start(
            self,
            update: Update,
            context: ContextTypes.DEFAULT_TYPE,
            ):
        self.trace('Received command: /start')
        if update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=config.BOT_GREETING,
                parse_mode=ParseMode.HTML,
                )

    async def command_help(
            self,
            update: Update,
            context: ContextTypes.DEFAULT_TYPE,
            ):
        self.trace('Received command: /help')
        if update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=(
                    "Available commands:\n\n"
                    "<code>/start</code> : start intereaction with the bot\n"
                    "<code>/help</code> : Show commands\n"
                    "<code>/status</code> : Show status and alive time\n"
                    "<code>/config</code> : See (some) config parameters\n"
                    "<code>/zen</code> : Show the Zen of Python\n"
                    ),
                parse_mode=ParseMode.HTML,
                )

    async def command_zen(
            self,
            update: Update,
            context: ContextTypes.DEFAULT_TYPE,
            ):
        self.trace('Received command: /zen')
        if update.effective_chat:
            text = '\n'.join(replies.THE_ZEN_OF_PYTHON)
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=text,
                parse_mode=ParseMode.HTML,
                )

    async def command_config(
            self,
            update: Update,
            context: ContextTypes.DEFAULT_TYPE,
            ):
        self.trace('Received command: /config')
        buff = [
            f'Probabilidad de responder: {config.VERBOSITY:.2f}',
            'Disparadores:',
            ]
        for keyword, _ in replies.get_all_keywords_and_replies():
            buff.append(f' - {keyword}')
        text = '\n'.join(buff)
        if update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=text,
                parse_mode=ParseMode.HTML,
                )

    async def welcome(
            self,
            update: Update,
            context: ContextTypes.DEFAULT_TYPE,
            ):
        self.trace('Received new user event')
        if update.message:
            new_member = update.message.new_chat_members[0]
            self.trace(
                'Waiting %s seconds until user completes captcha...',
                config.WELCOME_DELAY,
                )
            time.sleep(config.WELCOME_DELAY)
            membership_info = await context.bot.get_chat_member(
                update.message.chat_id,
                new_member.id,
                )
            if membership_info['status'] == 'left':
                self.trace(
                    'Skipping welcome message,'
                    ' user %s is no longer in the chat',
                    new_member.name,
                    )
                return
            msg = None
            if new_member.is_bot:
                msg = (
                    f"{new_member.name} is a *bot*\\!\\! "
                    "-> It could be kindly removed 🗑"
                    )
            else:
                if utils.is_bot(new_member):
                    await context.bot.delete_message(
                        update.message.chat_id,
                        update.message.message_id,
                    )
                    if update.chat_member:
                        if await update.chat_member.chat.ban_member(
                                user_id=new_member.id,
                                ):
                            msg = (
                                f"*{new_member.username}* has been banned"
                                " because I considered it a bot. "
                                )
                else:
                    msg = (
                        f"Welcome {new_member.name}\\!\\! "
                        "I am a friendly and polite *bot* 🤖"
                        )
            if msg:
                await update.message.reply_text(
                    msg,
                    parse_mode=telegram.constants.ParseMode('MarkdownV2'),
                    )
                self.trace('Sent welcome message for %s', new_member.name)

    async def reply(
            self,
            update: Update,
            context: ContextTypes.DEFAULT_TYPE,
            ):
        if config.bot_replies_enabled() and update.message:
            msg = update.message.text
            if msg:
                reply_text = replies.triggers_reply(msg)
                if reply_text:
                    self.trace('Sending reply: %s', reply_text)
                    await update.message.reply_text(reply_text)

    def run(self):
        self.trace('Starting bot')
        application = (
            ApplicationBuilder()
            .token(config.TELEGRAM_BOT_TOKEN)
            .build()
            )
        start_handler = CommandHandler('start', self.command_start)
        application.add_handler(start_handler)
        help_handler = CommandHandler('help', self.command_help)
        application.add_handler(help_handler)

        # Status handler
        status_handler = CommandHandler('status', self.command_status)
        application.add_handler(status_handler)

        # Zen Command
        application.add_handler(CommandHandler('zen', self.command_zen))

        # Config Command
        application.add_handler(CommandHandler('config', self.command_config))

        welcome_handler = MessageHandler(
            filters.StatusUpdate.NEW_CHAT_MEMBERS,
            self.welcome,
            )
        application.add_handler(welcome_handler)
        reply_handler = MessageHandler(
            filters.TEXT & (~filters.COMMAND),
            self.reply,
            )
        application.add_handler(reply_handler)
        self.trace('Bot is ready')
        application.run_polling(poll_interval=config.POLL_INTERVAL)


def main():
    """
    Arranca el bot
    """
    bot = DeckardBot()
    bot.run()


if __name__ == "__main__":
    main()
