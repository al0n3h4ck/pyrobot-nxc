import time
import pyrogram
from pyrogram import Client
from help.progress import progress
from help.adds import clean_name, upload_file, get_share_link
from config import Config
from db_json import db_mod_status, file_add_delete
from pyrogram.types import Message


@Client.on_message(pyrogram.filters.audio)
async def audio_handler(client: Client, message: Message):
    print("{} --> Envio un audio!".format(message.from_user.username))
    cola = 0
    if message.from_user.id not in Config.ADMINS:
        return
    else:
        if Config.JOB != 0:
            cola = await client.send_message(chat_id=message.from_user.id, text="Audio en cola...")
            
        try:
            Config.JOB += 1
            if cola != 0:
                await cola.delete()
            msg = await client.send_message(chat_id=message.chat.id,
                                            text="Audio detectado...",
                                            reply_to_message_id=message.message_id
                                            )
            print(message.audio.file_name)
            full_name = message.audio.file_name
            if full_name is None:
                ext = message.audio.mime_type.split("/")[1]
                full_name = message.audio.file_unique_id + "." + ext
            full_name = await clean_name(full_name)
            file = "./{}".format(full_name)
            print(full_name)
            start = time.time()
            await client.download_media(message=message, file_name=file, progress=progress, progress_args=(msg, start))
            await msg.delete()
            await upload_file(file, message.chat.id)
            ge = await client.send_message(chat_id=message.chat.id,
                                           text="Generando enlace de descarga...",
                                           disable_notification=True)
            direct_link = await get_share_link(full_name)
            num_id = file_add_delete(full_name)
            await ge.delete()
            await client.send_message(chat_id=message.from_user.id,
                                      text="**DESCARGA DIRECTA:**\n{}\n\n/delete_ID_{}".format(direct_link, str(num_id)))
            size = int(message.audio.file_size)
            db_mod_status(size)
            Config.JOB -= 1
        except Exception as e:
            print(e)
            Config.JOB -= 1
            await client.send_message(chat_id=message.from_user.id, text=f"{e}")