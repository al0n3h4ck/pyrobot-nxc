import re
import time
import requests
from pyrogram import Client, filters
from help.dl import AnyDL
from config import Config
from help.adds import upload_file, download_file, get_share_link, clean_name, filename_geturl
from db_json import db_mod_status, file_add_delete
from pyrogram.types import Message


@Client.on_message(filters.regex(pattern=".*http.*"))
async def link_handler(client: Client, message: Message):
    print("{} envio un enlace!".format(message.from_user.username))
    cola = 0
    if message.from_user.id not in Config.ADMINS:
        return
    else:
        if Config.JOB != 0:
            cola = await client.send_message(chat_id=message.from_user.id, text="Enlace en cola...")
        if cola != 0:
            await cola.delete()

        msg = await client.send_message(chat_id=message.from_user.id, text="Enlace detectado...")
        dl_client = AnyDL()
        url = message.text
        if 'drive.google.com' in url:
            try:
                link = re.findall(r'\bhttps?://drive\.google\.com\S+', url)[0]
            except IndexError:
                return await msg.edit("No es un enlace de Google Drive!")
            try:
                file_url, file_name = await dl_client.gdrive(url)
                print(file_url)
                print(file_name)
                file_name = await clean_name(file_name)
            except BaseException as e:
                return await msg.edit(f"No se pudo obtener el enlace de descarga directa de Google Drive: {e}")
            if file_url is None:
                return await msg.edit("No se pudo obtener el enlace de descarga directa de Google Drive")

        if "mediafire.com" in url:
            try:
                link = re.findall(r'\bhttps?://.*mediafire\.com\S+', url)[0]
            except IndexError:
                return await msg.edit("Link de Mediafire no compatible!")
            try:
                file_url, file_name, file_size, file_upload_date, caption_, scan_result = await dl_client.media_fire_dl(
                    url)
                file_name = await clean_name(file_name)
            except BaseException as e:
                return await msg.edit(f"Error al generar el enlace directo de descarga: {e}")
            if file_url is None:
                return await msg.edit("Error al generar el enlace directo de descarga")

        if "mega.nz" in url:
            try:
                link = re.findall(r'\bhttps?://.*mega\.nz\S+', url)[0]
            except IndexError:
                return await msg.edit("No es un enlace de Mega!")
            if "folder" in link:
                return await msg.edit("No se puede descargar carpetas :(")
            try:
                file_url, file_name, file_size = await dl_client.mega_dl(link)
                print(file_url)
                file_name = await clean_name(file_name)
                print(file_name)
            except BaseException as e:
                return await msg.edit(f"Error al generar el enlace directo de descarga de Mega: {e}")
            if file_url is None:
                return await msg.edit("Error al generar el enlace directo de descarga de Mega")

        if "anonfiles" in url:
            try:
                link = re.findall(r"\bhttps?://.*anonfiles\.com\S+", url)[0]
            except IndexError:
                return await msg.edit("No es un enlace de Anonfiles")
            try:
                file_url, file_size, file_name = await dl_client.anon_files_dl(link)
                file_name = await clean_name(file_name)
            except BaseException as e:
                return await msg.edit(f"Error al generar el enlace de descarga directo de Anonfiles: {e}")
            if file_url is None:
                return await msg.edit("Error al generar el enlace de descarga directo de Anonfiles")

        else:
            resp = requests.get(url=url, allow_redirects=True, stream=True)
            print(resp.status_code)
            full_name = await filename_geturl(url, resp)
            print(full_name)
            file_url = url
            full_name = full_name[1]
            file_name = await clean_name(full_name)
            print("Clean filename: " + full_name)

        try:
            Config.JOB += 1
            file, size_db = await download_file(msg, file_url, file_name)
            await msg.delete()
            await upload_file(file, message.chat.id)
            ge = await client.send_message(chat_id=message.chat.id,
                                           text="Generando enlace de descarga...",
                                           disable_notification=True)
            direct_link = await get_share_link(file)
            num_id = file_add_delete(file)
            await ge.delete()
            await client.send_message(chat_id=message.from_user.id,
                                      text="**DESCARGA DIRECTA:**\n{}\n\n/delete_ID_{}".format(direct_link,
                                                                                           str(num_id)))
            db_mod_status(size_db)
            Config.JOB -= 1
            return
        except Exception as er:
            print(er)
            await client.send_message(chat_id=message.from_user.id,
                                      text="Error:\n{}".format(er))
            Config.JOB -= 1
