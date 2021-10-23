import math
import os
import time
import unicodedata
from pyrogram.errors import MessageNotModified
from help.progress import humanbytes, TimeFormatter
import requests
from config import Config
from tqdm.utils import CallbackIOWrapper
from pathlib import Path
from tqdm.contrib.telegram import tqdm

CHUNK_SIZE = 10240
TIMEOUT: float = 60

header = {
    'Connection': 'keep-alive',
    'sec-ch-ua': '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"',
    'Accept': 'application/json, text/plain, */*',
    'requesttoken': '',
    'sec-ch-ua-mobile': '?0',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4389.90 Safari/537.36',
    'Content-Type': 'application/json;charset=UTF-8',
    'Origin': 'https://nube.ucf.edu.cu',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Dest': 'empty',
    'Accept-Language': 'en-US,en;q=0.9,es;q=0.8'
}


#async def upload_file_old(file):
#    print("Func. upload_file")
#    with open(file, 'rb') as upload:
#        with requests.Session() as request:
#            request.auth = (Config.USER, Config.PASSWORD)
#            conn = request.put('https://nube.ucf.edu.cu/remote.php/webdav/{}'.format(file), data=upload)
#            print(conn.status_code)
#            os.unlink(file)
#    print('Upload Ok!')


async def upload_file(file, chat_id):
    filename_path = Path(f"{file}")
    print("Func. upload_file")
    # with open(file, 'rb') as upload:
    with requests.Session() as request:
        request.auth = (Config.USER, Config.PASSWORD)
        size = filename_path.stat().st_size if filename_path.exists() else 0
        print(size)
        with tqdm(token=Config.BOT,
                  chat_id=chat_id,
                  total=size,
                  desc="Subiendo... ",
                  mininterval=3.0,
                  unit="B",
                  unit_scale=True,
                  bar_format="{desc}{percentage:3.0f}% / {rate_fmt}{postfix}",
                  unit_divisor=CHUNK_SIZE,
                  ) as t, open(filename_path, "rb") as fileobj:
            wrapped_file = CallbackIOWrapper(t.update, fileobj, "read")
            with request.put(
                    url="https://nube.ucf.edu.cu/remote.php/webdav/{}".format(file),
                    data=wrapped_file,  # type: ignore
                    headers=header,
                    timeout=TIMEOUT,
                    stream=True,
            ) as resp:
                print(resp.status_code)
                resp.raise_for_status()
                t.tgio.delete()
                print("UPLOAD OK!")


async def get_share_link(full_name):
    with requests.Session() as request:
        request.auth = (Config.USER, Config.PASSWORD)
        response = request.get('https://nube.ucf.edu.cu/index.php/apps/dashboard/')
        i = response.content.index(b'token=')
        tok = str(response.content[i + 7:i + 96])[2:-1]
        header.update({'requesttoken': tok})
        data = '{"path":"' + f'/{full_name}' + '","shareType":3, "password":"' + f'{Config.LINK_PASSWORD}' + '"}'
        response = request.post('https://nube.ucf.edu.cu/ocs/v2.php/apps/files_sharing/api/v1/shares',
                                headers=header, cookies=response.cookies, data=data)
        url = response.json()
    try:
        url = url['ocs']['data']['url']
        url = url + "/download/" + full_name
    except Exception as e:
        print(f'Error getting share link: {e}')
        url = "Error: {}".format(e)
    return url


async def delete_file(filename):
    with requests.Session() as request:
        request.auth = (Config.USER, Config.PASSWORD)
        url = "https://nube.ucf.edu.cu/remote.php/webdav{}".format(filename)
        req = request.delete(url=url)
        return req.status_code


async def filename_geturl(url, resp):
    if url.find("heroku") != -1:
        print("heroku")
        return await get_heroku_bot(resp, url)
    else:
        file = url.split("/", -1)[-1]
        if file.find("?") != -1:
            file = file.split("?", -1)[0]
        if file.find(".") == -1:
            try:
                file = resp.headers["Content-Disposition"].split("", 1)[1].split("=", 1)[1][1:-1]
            except Exception as err:
                print(err)
                if url.find("checker") != -1:
                    file += ".mp4"
                else:
                    file += ".ext"
        return ["direct", file]


async def get_heroku_bot(resp, url):
    print(resp.headers)
    try:
        file = resp.headers["Conetnt-Disposition"].split(" ", 1)[1].split("=", 1)[1][1:-1]
    except Exception as err:
        print(err)
        try:
            # ext = resp.headers["Content-Type"]
            # file = "heroku_file.{}".format(ext.split("/", -1)[1])
            file_name = url.split("/")
            file = file_name[-1]
        except Exception as error:
            print(error)
            file = "defaul_name.ext"
    return ["heroku", file]


async def clean_name(name):
    full_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    full_name = full_name.replace(" ", "_")
    full_name = full_name.replace("%20", "_")
    full_name = full_name.replace("(", "")
    full_name = full_name.replace(")", "")
    full_name = full_name.replace("$", "")
    full_name = full_name.replace("%", "_")
    full_name = full_name.replace("@", "_")
    full_name = full_name.replace("/", "")
    full_name = full_name.replace("|", "")
    full_name = full_name.replace("..", ".")
    return full_name


async def download_file(message, url, file_name):
    start = time.time()
    with open(file_name, mode='wb') as f:
        with requests.Session() as session:
            with session.get(url, stream=True) as r:
                total_length = r.headers.get('content-length') or r.headers.get("Content-Length")
                current = 0
                if total_length is None:
                    await message.edit(f"Descargando archivo... \nArchivo: {file_name}\nTamaño: Desconocido")
                    f.write(r.content)
                    total_length = 0
                else:
                    total = int(total_length)
                    for chunk in r.iter_content(1024*1204*15):
                        now = time.time()
                        diff = now - start
                        current += len(chunk)
                        percentage = current * 100 / total
                        speed = current / diff
                        elapsed_time = round(diff) * 1000
                        time_to_completion = round((total - current) / speed) * 1000
                        estimated_total_time = elapsed_time + time_to_completion
                        elapsed_time = TimeFormatter(milliseconds=elapsed_time)
                        estimated_total_time = TimeFormatter(milliseconds=estimated_total_time)
                        progressed = "[{0}{1}] \n\nProgreso: {2}%\n".format(
                            ''.join(["█" for i in range(math.floor(percentage / 5))]),
                            ''.join(["░" for i in range(20 - math.floor(percentage / 5))]),
                            round(percentage, 2))
                        tmp = progressed + "Descargado: {0}\nTotal: {1}\nVelocidad: {2}/s\nFaltan: {3}\n".format(
                            humanbytes(current),
                            humanbytes(total),
                            humanbytes(speed),
                            # elapsed_time if elapsed_time != '' else "0 s",
                            estimated_total_time if estimated_total_time != '' else "0 s")
                        f.write(chunk)
                        try:
                            await message.edit("Descargando...\n{}".format(tmp))
                        except MessageNotModified:
                            time.sleep(5.0)
                            pass
    return file_name, int(total_length)
