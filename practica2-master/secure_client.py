"""
    Fichero:
        secure_client.py
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


from argparse import ArgumentParser
import users
import file

token = '6d5BF4273Af80eE1'  # sustituir por el token de usuario propio


def main():
    """
    Bucle principal de la aplicación. Se encarga de parsear los argumentos
    haciendo uso de argparse y lanzar las distintas funciones en función de
    ello.

    """
    args_parser = ArgumentParser()

    # Gestión de usuarios e identidades
    args_parser.add_argument("--create_id", nargs=2,
                             metavar=("nombre", "email"))
    args_parser.add_argument("--search_id", nargs=1, metavar=("cadena"))
    args_parser.add_argument("--delete_id", nargs=1, metavar=("id"))

    # Subida y descarga de ficheros
    args_parser.add_argument("--upload", nargs=1, metavar=("fichero"))
    args_parser.add_argument("--source_id", nargs=1, metavar=("id"))
    args_parser.add_argument("--dest_id", nargs=1, metavar=("id"))
    args_parser.add_argument("--list_files", action="store_true")
    args_parser.add_argument("--download", nargs=1, metavar=("id_fichero"))
    args_parser.add_argument("--delete_file", nargs=1, metavar=("id_fichero"))

    # Cifrado y firma de ficheros local
    args_parser.add_argument("--encrypt", nargs=1, metavar=("fichero"))
    args_parser.add_argument("--sign", nargs=1, metavar=("fichero"))
    args_parser.add_argument("--enc_sign", nargs=1, metavar=("fichero"))

    args = args_parser.parse_args()

    # Gestión de usuarios e identidades
    if args.create_id:
        users.create_id(token, name=args.create_id[0], email=args.create_id[1])
    elif args.search_id:
        users.search_id(token, cadena=args.search_id[0])
    elif args.delete_id:
        users.delete_id(token, id=args.delete_id[0])
    # Subida y descarga de ficheros
    elif args.upload and args.dest_id:
        file.upload(token, file_name=args.upload[0], dest_id=args.dest_id[0])
    elif args.download and args.source_id:
        file.download(token, id_fichero=args.download[0], source_id=args.source_id[0])
    elif args.list_files:
        file.list_files(token)
    elif args.delete_file:
        file.delete_file(token, file_id=args.delete_file[0])
    # Cifrado y firma de ficheros local
    elif args.encrypt and args.dest_id:
        file.encrypt_file(token, args.encrypt[0], args.dest_id[0])
    elif args.sign:
        file.sign_file(args.sign[0])
    elif args.enc_sign and args.dest_id:
        file.enc_sign_file(token, args.enc_sign[0], dest_id=args.dest_id[0])
    else:
        print("El comando no existe.")


if __name__ == "__main__":
    main()
