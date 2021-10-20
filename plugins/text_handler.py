from config import Config
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from db_json import status_db, files_shared, get_file_share, clean_file_s, get_filename_delete, del_s, back_list
from help.progress import humanbytes
from help.adds import delete_file, header
from nextcloud import NextCloud
from nextcloud.requester import Requester
import requests
from bs4 import BeautifulSoup


@Client.on_message(filters.command("start") & filters.user(Config.ADMINS))
async def start(client: Client, message: Message):
    # fuser = message.from_user.id
    # if fuser not in Config.ADMINS:
    #   return
    await client.send_message(
        chat_id=message.chat.id,
        text="Bienvenido @{}".format(message.from_user.username),
        disable_web_page_preview=True,
        reply_to_message_id=message.message_id
    )


@Client.on_message(filters.command("status") & filters.user(Config.ADMINS))
async def status(client: Client, message: Message):
    print(f"{message.from_user.first_name} ejecuto el comando status!")
    if message.from_user.id == Config.ADMINS[0]:
        # <p id="quotatext">105.3 MB de 2 GB usados</p>

        with requests.Session() as session:
            session.auth = (Config.USER, Config.PASSWORD)
            url = "https://nube.uclv.cu/apps/files/"
            resp = session.get(url=url, headers=header)
            soup = BeautifulSoup(resp.content, "html5lib")
            space = soup.find(name="p", attrs={"id": "quotatext"})
            txt = space.text
            print(txt.upper())

        files_up, files_size = status_db()
        files_up = str(files_up)
        files_size = int(files_size)
        uso = "NO"
        if Config.JOB == 1:
            uso = "SI"
        await client.send_message(chat_id=message.from_user.id,
                                  text=f"**ESTADISTICAS DE USO**\n\nEN USO: {uso}\nCANT. DE ARCHIVOS: {files_up}\nDATOS SUBIDOS: {humanbytes(files_size)}\n\n**USO DE DATOS EN LA NUBE:**\n\n{txt.upper()}")
    else:
        files_up, files_size = status_db()
        files_up = str(files_up)
        files_size = int(files_size)
        uso = "NO"
        if Config.JOB == 1:
            uso = "SI"
        await client.send_message(chat_id=message.from_user.id,
                                  text=f"**ESTADISTICAS DE USO**\n\nEN USO: {uso}\nCANT. DE ARCHIVOS: {files_up}\nDATOS SUBIDOS: {humanbytes(files_size)}")


@Client.on_message(filters.regex(pattern=".*/delete_ID_.*"))
async def delete_handler(client: Client, message: Message):
    if message.from_user.id not in Config.ADMINS:
        return
    else:
        try:
            msg = await client.send_message(chat_id=message.from_user.id, text="Eliminando archivo...")
            del_msg = message.text
            id_file = int(del_msg[11:])
            filename = get_filename_delete(id_file)
            filename = f"/{filename}"
            code = await delete_file(filename)
            print(code)
            borrado = "se eliminó correctamente!"
            if code != 204:
                borrado = "no se eliminó, vuelve a intentarlo :("
            await msg.delete()
            await client.send_message(chat_id=message.from_user.id, text="El archivo {} {}".format(
                filename.split("/")[-1], borrado), disable_notification=True)
            return
        except Exception as error:
            print(error)
            await client.send_message(chat_id=message.from_user.id, text="{}".format(error))
            return


@Client.on_message(filters.command("shares"))
async def shares(client: Client, message: Message):
    print("{} ejecuto el comando share!".format(message.from_user.first_name))
    if message.from_user.id not in Config.ADMINS:
        return
    else:
        try:
            h = Requester
            h.headers.update(header)
            m = await client.send_message(chat_id=message.chat.id, text="Espere un momento...")
            with NextCloud(endpoint="https://nube.uclv.cu/", user=Config.USER, password=Config.PASSWORD) as nxc:
                nxc.login()
                shares = nxc.get_shares()
                list_share = shares.json_data
                share_txt = "**ARCHIVOS COMPARTIDOS**"
                buttons = []
                id_files = 0
                for s in list_share:
                    if s["item_type"] == "file" and s["share_type"] == 3:
                        nombre = s["path"].split("/")[-1]
                        url = s["url"]
                        # print("Path: {0}\nTipo: {1} -> [LINK]({2}{0})\n\n".format(s["path"], s["item_type"],
                        # s["url"])) share_lista += "**Nombre:** {0}\nDescarga directa: [LINK]({1}/download/{
                        # 0})\n\n".format(nombre, s["url"])
                        link = f"{url}/download/{nombre}"
                        path = s["path"]
                        share_list = [path, link]
                        data = f"file_{id_files}"
                        files_shared(data, share_list)
                        buttons.append([InlineKeyboardButton(text=nombre, callback_data=data)])
                        id_files += 1
                buttons.append([InlineKeyboardButton(text="CERRAR", callback_data="cerrar")])
                await m.delete()
                await client.send_message(chat_id=message.chat.id, text=share_txt,
                                          reply_markup=InlineKeyboardMarkup(buttons),
                                          parse_mode="markdown",
                                          disable_web_page_preview=True)
        except Exception as e:
            await client.send_message(chat_id=message.chat.id, text="Error: {}".format(e))


@Client.on_message(filters.command("kill"))
async def kill(client: Client, message: Message):
    print("{} ejecuto el comando share!".format(message.from_user.first_name))
    if message.from_user.id in Config.ADMINS:
        try:
            text = message.command
            print(text)
            filename = text[1]
            code = await delete_file(filename)
            print(code)
            borrado = "se eliminó correctamente!"
            if code != 204:
                borrado = "no se eliminó, vuelve a intentarlo :("
            await client.send_message(chat_id=message.from_user.id,
                                      text="El archivo {} {}".format(filename.split("/")[-1], borrado),
                                      disable_notification=True)

        except Exception as er:
            await client.send_message(chat_id=message.chat.id, text=str(er))


@Client.on_callback_query(filters.regex(r"^file"))
async def file_get(client: Client, query: CallbackQuery):
    print("File share!")
    try:
        msg = query.message
        id_user = query.message.chat.id
        await msg.delete()
        data = query.data
        path, link = get_file_share(data)
        filename = path.split("/")[-1]

        await client.send_message(chat_id=id_user,
                                  text="**ARCHIVO COMPARTIDO**\n\n**Nombre:** {}\n\nDescarga directa: {}".format(
                                      filename, link),
                                  parse_mode="markdown",
                                  disable_web_page_preview=True,
                                  reply_markup=InlineKeyboardMarkup(
                                      [
                                          [InlineKeyboardButton(text="ELIMINAR", callback_data="del_{}".format(data))],
                                          [
                                              InlineKeyboardButton(text="ATRÁS", callback_data="back"),
                                              InlineKeyboardButton(text="CERRAR", callback_data="cerrar")
                                          ]
                                      ]
                                  ))
    except Exception as er:
        print(er)
        await client.send_message(chat_id=query.message.chat.id, text=str(er))


@Client.on_callback_query(filters.regex(r"^del_"))
async def file_del(client: Client, query: CallbackQuery):
    print("Eliminar!")
    try:
        msg = query.message
        user_id = msg.chat.id
        await msg.delete()
        data = query.data
        key = data[4:]
        path, link = get_file_share(key)
        code = await delete_file(path)
        print(code)
        borrado = "se eliminó correctamente!"
        if code != 204:
            borrado = "no se eliminó, vuelve a intentarlo :("
        await client.send_message(chat_id=user_id,
                                  text="El archivo {} {}".format(path.split("/")[-1], borrado),
                                  reply_markup=InlineKeyboardMarkup([
                                      [InlineKeyboardButton(text="ATRÁS", callback_data="back"),
                                       InlineKeyboardButton(text="CERRAR", callback_data="cerrar")
                                       ]
                                  ]),
                                  disable_notification=True)
        del_s(key)
    except Exception as err:
        print(err)
        await client.send_message(chat_id=query.message.from_user.id, text=str(err))


@Client.on_callback_query(filters.regex(r"^cerrar$"))
async def cerrar(client: Client, query: CallbackQuery):
    print("Cerrar!")
    msg = query.message
    await msg.delete()
    clean_file_s()


@Client.on_callback_query(filters.regex(r"^back$"))
async def back(client: Client, query: CallbackQuery):
    print(f"{query.message.from_user.first_name} -> Cerrar!")
    msg = query.message
    await msg.delete()
    try:
        dic_files = back_list()
        share_txt = "**ARCHIVOS COMPARTIDOS**"
        butt = []
        for k, v in dic_files.items():
            nombre = v[0].split("/")[-1]
            butt.append([InlineKeyboardButton(text=nombre, callback_data=k)])

        butt.append([InlineKeyboardButton(text="CERRAR", callback_data="cerrar")])
        await client.send_message(chat_id=msg.chat.id, text=share_txt,
                                  reply_markup=InlineKeyboardMarkup(butt),
                                  parse_mode="markdown",
                                  disable_web_page_preview=True)
    except Exception as err:
        print(err)
        await client.send_message(chat_id=query.message.chat.id,
                                  text=str(err))
