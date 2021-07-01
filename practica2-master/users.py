"""
    Fichero:
        user.py
    Autores:
        Antonio Altea Segovia
        Raul Cuesta Barroso
    Asignatura: 
        Redes-II
    Grupo:
        2311
    Pareja:
        14
"""


import encryption
from Crypto.PublicKey import RSA
import requests_manager as rm

URL = "users/"


def create_id(token, name, email):
    """
    Manda la petición de creación de registro de usuario. Genera el par de
    claves privada y pública.

    Atributos:
        token (str): token de usuario 
        name (str): nombre de usuario
        email (str): email del usuario
    """

    encryption.generate_keys() # generación de claves

    public_key = encryption.read_public_key()
    
    # diccionario con los atributos
    args = {"nombre": name, "email": email,
            "publicKey": public_key.export_key("OpenSSH").decode("utf-8"), }
    
    # envio con el gestor de peticiones
    response = rm.send_requests(token, URL + "register", args)

    data = response.json()
    if response.status_code == 200:
        print("Usuario creado con el id {} en el momento {}".format(
            data["userID"], data["ts"]))
    else:
        rm.print_server_error(data)


def search_id(token, cadena):
    """
    Manda la petición de búsqueda de usuarios dada una cadena de texto

    Atributos:
        token (str): token de usuario 
        cadena (str): cadena de texto a buscar
    """

    print("Buscando usuario '{}' en el servidor...".format(cadena))
    args = {"data_search": cadena, }

    response = rm.send_requests(token, URL + "search", args)

    data = response.json()
    if response.status_code == 200:
        if len(data) < 1:
            print("OK\nNo se encontró ningún usuario.")
        else:
            print("OK\n{} usuarios encontrados:".format(len(data)))
            cont = 0
            for user in data:
                print("[{}] {}, {}, ID: {}".format(
                    cont, user["nombre"], user["email"], user["userID"]))
            cont += 1
    else:
        rm.print_server_error(data)


def delete_id(token, id):
    """
    Manda la petición de eliminación de usuario

    Atributos:
        token (str): token de usuario 
        id (str): id del usuario a eliminar
    """

    args = {"userID": id, }

    response = rm.send_requests(token, URL + "delete", args)

    data = response.json()
    if response.status_code == 200:
        print("Borrado usuario con ID {}".format(data["userID"]))
    else:
        rm.print_server_error(data)


def get_public_key(token, id):
    """
    Manda la petición de obtención de la clave pública de un usario

    Atributos:
        token (str): token de usuario 
        id (str): id del usuario a buscar

    Returns:
        None si no se encuentra el usuario o se produce un error
        (str) Clave pública del usuario encontrada
    """

    args = {"userID": id, }

    response = rm.send_requests(token, URL + "getPublicKey", args)

    data = response.json()
    if response.status_code == 200:
        return data["publicKey"]
    else:
        (data)
        return None
