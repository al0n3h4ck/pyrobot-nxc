import pyrogram
from pyrogram import idle
from config import Config

if __name__ == "__main__":
    api_id = Config.API_ID
    api_hash = Config.API_HASH
    bot = Config.BOT
    plugins = dict(
        root="plugins"
    )

    app = pyrogram.Client(
        session_name="nxc_cloudbot",
        api_id=api_id,
        api_hash=api_hash,
        bot_token=bot,
        workers=6,
        plugins=plugins
    )

    app.run()
