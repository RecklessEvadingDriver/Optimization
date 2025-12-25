from pyrogram import Client, enums
from pyrogram.types import LinkPreviewOptions
from asyncio import Lock

from .. import LOGGER
from .config_manager import Config
from .token_utils import parse_bot_tokens


class TgClient:
    _lock = Lock()
    bot = None
    extra_bots = []
    _bot_cycle = -1
    user = None
    NAME = ""
    ID = 0
    IS_PREMIUM_USER = False
    MAX_SPLIT_SIZE = 4194304000

    @classmethod
    async def start_bot(cls):
        LOGGER.info("Creating client(s) from BOT_TOKEN")
        tokens = parse_bot_tokens(Config.BOT_TOKEN)
        if not tokens:
            raise ValueError("BOT_TOKEN variable is missing!")
        main_token = tokens[0]
        cls.ID = main_token.split(":", 1)[0]
        cls.bot = Client(
            cls.ID,
            Config.TELEGRAM_API,
            Config.TELEGRAM_HASH,
            proxy=Config.TG_PROXY,
            bot_token=main_token,
            workdir="/app",
            parse_mode=enums.ParseMode.HTML,
            max_concurrent_transmissions=10,
            max_message_cache_size=15000,
            max_topic_cache_size=15000,
            sleep_threshold=0,
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )
        await cls.bot.start()
        cls.NAME = cls.bot.me.username
        cls.extra_bots = []
        for idx, token in enumerate(tokens[1:], start=1):
            LOGGER.info(f"Creating extra bot client #{idx}")
            extra = Client(
                f"{cls.ID}_{idx}",
                Config.TELEGRAM_API,
                Config.TELEGRAM_HASH,
                proxy=Config.TG_PROXY,
                bot_token=token,
                workdir="/app",
                parse_mode=enums.ParseMode.HTML,
                max_concurrent_transmissions=10,
                max_message_cache_size=15000,
                max_topic_cache_size=15000,
                sleep_threshold=0,
                link_preview_options=LinkPreviewOptions(is_disabled=True),
            )
            await extra.start()
            cls.extra_bots.append(extra)
        cls._bot_cycle = -1

    @classmethod
    async def start_user(cls):
        if Config.USER_SESSION_STRING:
            LOGGER.info("Creating client from USER_SESSION_STRING")
            try:
                cls.user = Client(
                    "user",
                    Config.TELEGRAM_API,
                    Config.TELEGRAM_HASH,
                    proxy=Config.TG_PROXY,
                    session_string=Config.USER_SESSION_STRING,
                    workdir="/app",
                    parse_mode=enums.ParseMode.HTML,
                    sleep_threshold=60,
                    max_concurrent_transmissions=10,
                    max_message_cache_size=15000,
                    max_topic_cache_size=15000,
                    link_preview_options=LinkPreviewOptions(is_disabled=True),
                )
                await cls.user.start()
                cls.IS_PREMIUM_USER = cls.user.me.is_premium
            except Exception as e:
                LOGGER.error(f"Failed to start client from USER_SESSION_STRING. {e}")
                cls.IS_PREMIUM_USER = False
                cls.user = None
        cls.MAX_SPLIT_SIZE = 4194304000

    @classmethod
    async def stop(cls):
        async with cls._lock:
            if cls.bot:
                await cls.bot.stop()
            for extra in cls.extra_bots:
                await extra.stop()
            if cls.user:
                await cls.user.stop()
            LOGGER.info("Client(s) stopped")

    @classmethod
    async def reload(cls):
        async with cls._lock:
            await cls.bot.restart()
            for extra in cls.extra_bots:
                await extra.restart()
            if cls.user:
                await cls.user.restart()
            LOGGER.info("Client(s) restarted")

    @classmethod
    def next_bot_client(cls):
        if not cls.extra_bots:
            return cls.bot
        cls._bot_cycle = (cls._bot_cycle + 1) % (len(cls.extra_bots) + 1)
        if cls._bot_cycle == 0:
            return cls.bot
        return cls.extra_bots[cls._bot_cycle - 1]
