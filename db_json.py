import json


def delete_id():
    with open("bot.json", "r") as db:
        data = json.loads(db.read())
        print(data)
        dic = dict(data)
        num = dic["delete_id"]["file_id"] + 1
        dic["delete_id"]["file_id"] = num
        print(dic["delete_id"]["file_id"])
        json.dumps(dic)
        print(dic)
        with open("bot.json", "w") as file:
            json.dump(dic, file, indent=4)
        return int(dic["delete_id"]["file_id"])


def file_add_delete(filename: str):
    id = delete_id()
    with open("bot.json", "r") as db:
        data = json.loads(db.read())
        data = dict(data)
        data["files_delete"][id] = filename
        with open("bot.json", "w") as file:
            json.dump(data, file, indent=4)
            return id


def get_filename_delete(id):
    id = str(id)
    with open("bot.json", "r") as db:
        data = json.loads(db.read())
        data = dict(data)
        return str(data["files_delete"][id])


def db_mod_status(size):
    with open("bot.json", "r") as db:
        data = json.loads(db.read())
        print(data)
        dic = dict(data)
        dic["status"]["files_up"] += 1
        dic["status"]["files_size"] += size
        with open("bot.json", "w") as file:
            json.dump(dic, file, indent=4)


def status_db():
    with open("bot.json", "r") as db:
        data = json.loads(db.read())
        data = dict(data)
        return data["status"]["files_up"], data["status"]["files_size"]


# Guarda los archivos de la nube en un diccionario
def files_shared(key: str, file_s: list):
    with open("bot.json", "r") as db:
        data = json.loads(db.read())
        data = dict(data)
        data["files_shares"][key] = file_s
        with open("bot.json", "w") as file:
            json.dump(data, file, indent=4)


# Retorna un archivo de la nube almacenado en el diccionario
def get_file_share(key):
    key = str(key)
    with open("bot.json", "r") as db:
        data = json.loads(db.read())
        data = dict(data)
        path = str(data["files_shares"][key][0])
        link = str(data["files_shares"][key][1])
        return path, link


# Limpia el diccionario que contiene los archivos de la nube
def clean_file_s():
    with open("bot.json", "r") as db:
        data = json.loads(db.read())
        data = dict(data)
        data["files_shares"] = {}
        with open("bot.json", "w") as file:
            json.dump(data, file, indent=4)


# Borra un archivo del diccionario
def del_s(key):
    with open("bot.json", "r") as db:
        data = json.loads(db.read())
        data = dict(data)
        del data["files_shares"][key]
        with open("bot.json", "w") as file:
            json.dump(data, file, indent=4)


# Devuelve un diccionario con los datos de los archivos de la nube cargados previamente
def back_list():
    with open("bot.json", "r") as db:
        data = json.loads(db.read())
        data = dict(data)
        dic_list = data["files_shares"]
        return dict(dic_list)
