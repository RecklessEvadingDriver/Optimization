from bot.core.config_manager import Config

DRIVE_DISABLED_MSG = "Drive features are disabled in Telegram-only mode."


def drive_disabled() -> bool:
    return Config.TELEGRAM_ONLY
