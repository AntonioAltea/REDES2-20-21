"""
    Fichero:
        request_manager.py
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


import requests


URL = "https://vega.ii.uam.es:8080/api/"


def send_requests(token, url_module, args):
    """
    Envía una petición http al servidor de la aplicación

    Parámetros:
        token (str): token privado del usuario
        url_module(str): módulo específico de la dirección http
        args (dic): diccionario de argumentos de la petición http

    Returns:
        (str): Respuesta obtenida del servidor
    """

    headers = {"Authorization": "Bearer " + token}
    response = requests.post(
        url=URL + url_module, headers=headers, json=args)

    return response

def send_requests_file(token, url_module, file):
    """
    Envía una petición http al servidor específica para envío de ficheros

    Parámetros:
        token (str): token privado del usuario
        url_module(str): módulo específico de la dirección http
        args (dict): diccionario de argumentos de la petición http

    Returns:
        (str): Respuesta obtenida del servidor
    """
    headers = {"Authorization": "Bearer " + token}
    response = requests.post(
        url=URL + url_module, headers=headers, files={'ufile': file})

    return response


def print_server_error(data):
    """
    Imprime el error recibido de una petición http

    Parámetros:
        data (dict): diccionario de la respuesta del servidor conteniendo el error
    """
    print("{}, {}, {}".format(data["http_error_code"],
                                    data["error_code"], data["description"]))
