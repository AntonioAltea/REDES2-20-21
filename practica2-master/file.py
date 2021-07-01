"""
    Fichero:
        file.py
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

import users
import encryption
import requests_manager as rm
import os


URL = "files/"


def upload(token, file_name, dest_id):

    """
    Manda la petición de creación de subida de ficheros a un usuario

    Atributos:
        token (str): token de usuario 
        file_name (str): nombre del fichero a subir
        dest_id (str): id del usuario destino
    """

    # abrimos el fichero
    with open(file_name, 'rb') as file:
        file_content = file.read()
    file.close()
    

    # obtención de clave pública destino
    dest_key = users.get_public_key(token, dest_id)
    
    #firma y encriptado del fichero
    encrypted_content = encryption.enc_sign_content(file_content, dest_key)

    # creación del nuevo fichero
    new_name_split = file_name.split(".")
    new_file_name = new_name_split[0] + "_send." + new_name_split[1]
    new_file = open(new_file_name, 'wb')
    new_file.write(encrypted_content)
    new_file.close()
    new_file = open(new_file_name, "rb")

    # enviamos el nuevo fichero y lo borramos del sistema
    response = rm.send_requests_file(token, URL + "upload", new_file)
    new_file.close()
    os.remove(new_file_name)

    # gestionamos la respuesta
    data = response.json()
    if response.status_code == 200:
        print("Enviado fichero con ID {} y tamaño {}".format(
            data["file_id"], data["file_size"]))
    else:
        rm.print_server_error(data)


def download(token, id_fichero, source_id):
    """
    Manda la petición de descarga de un fichero

    Atributos:
        token (str): token de usuario 
        id_fichero (str): id del fichero a descargar
        source_id (str): id del usuario fuente
    """

    args = {"file_id": id_fichero,}
    response = rm.send_requests(token, URL + "download", args)
    
    data = response.json
    if response.status_code == 200:
        print("Descargado fichero con ID: {}".format(id_fichero))

        headers_disp = response.headers["Content-Disposition"]
        
        # split para obtener el tipo de fichero
        headers_disp_split = headers_disp.split(".")
        
        # obtención de la clave pública del usuario fuente
        source_key = users.get_public_key(token, source_id)

        # desencriptado del contenido y guardado en nuevo fichero
        decrypted_download = encryption.decrypt_file_content(response.content, source_key)
        new_name = "download_{}.{}".format(id_fichero, headers_disp_split[1][:-1])
        with open(new_name, "wb") as new_file:
            new_file.write(decrypted_download)

    else:
        rm.print_server_error(data)


def list_files(token):
    """
    Manda la petición de listado de ficheros. Muestra por pantalla el listado
    de ficheros enviados al usuario

    Atributos:
        token (str): token de usuario 
    """

    response = rm.send_requests(token, URL + "/list", None)

    data = response.json()
    if response.status_code == 200:
        print("OK\n{} ficheros encontrados:".format(data["num_files"]))
        cont=0
        for file_info in data["files_list"]:
            print("[{}] {} {}".format(cont, file_info["fileID"], file_info["fileName"]))
        cont += 1


def delete_file(token, file_id):
    """
    Manda la petición de borrado de ficheros enviados a nuestro usuario

    Atributos:
        token (str): token de usuario
        file_id (str): id del fichero a eliminar
    """

    args={"file_id": file_id}
    response=rm.send_requests(token, URL + "/delete", args)

    data=response.json()
    if response.status_code == 200:
        print("Eliminado fichero con ID {}".format(data["file_id"]))
    else:
        rm.print_server_error(data)

def sign_file(file_name):

    """
    Firma un fichero con la clave privada y guarda el resultado en uno nuevo.

    Atributos:
        file_name (str): nombre del fichero a firmar
    """

    with open(file_name, 'rb') as original_file:
        original_content = original_file.read()
    original_file.close

    signed_content = encryption.sign_file_content(original_content)

    new_name_split = file_name.split(".")
    new_file_name = new_name_split[0] + "_signed." + new_name_split[1]
    with open(new_file_name, 'wb') as new_file:
        new_file.write(signed_content)
    new_file.close()


def encrypt_file(token, file_name, dest_id):
    """
    Encripta un fichero con la clave pública de un usuario y guarda el
    resultado en uno nuevo.

    Atributos:
        token (str): token del usuario
        file_name (str): nombre del fichero a encriptar
        dest_id (str): id del usuario destino
    """

    with open(file_name, 'rb') as original_file:
        original_content = original_file.read()
    original_file.close()

    # obtiene la clave pública del usuario destino
    dest_key = users.get_public_key(token, dest_id)

    encrypted_content = encryption.enc_file_content(original_content, dest_key)

    new_name_split = file_name.split(".")
    new_file_name = new_name_split[0] + "_encrypted." + new_name_split[1]
    with open(new_file_name, 'wb') as new_file:
        new_file.write(encrypted_content)
    new_file.close()

def enc_sign_file(token, file_name, dest_id):
    """
    Firma un fichero con la clave privada y lo encripta con la pública de un
    usuario. Después guarda el resultado en uno nuevo.

    Atributos:
        token (str): token del usuario
        file_name (str): nombre del fichero a encriptar
        dest_id (str): id del usuario destino
    """

    with open(file_name, 'rb') as original_file:
        original_content = original_file.read()
    original_file.close()

    dest_key = users.get_public_key(token, dest_id)
    encrypted_content = encryption.enc_sign_content(original_content, dest_key)

    new_name_split = file_name.split(".")
    new_file_name = new_name_split[0] + "_signed_encrypted." + new_name_split[1]
    with open(new_file_name, 'wb') as new_file:
        new_file.write(encrypted_content)
    new_file.close()