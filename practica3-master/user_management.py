"""
    Fichero:
        user_management.py
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
import socket

MAX_STR = 8196
PORT = 8081


class User(object):
    '''
    La clase usuario contiene los metodos que se comunican con el servidor
    vega para realizar varias funciones de la app indicadas en cada metodo.

    Atributos:
        in_call (boolean): valor que indica si un usuario esta en una llamada
        port (int): puerto que va a usar el usuario para registrarse, no lo
                    introduce manualmente para facilitar el registro
        ip (str):  Ip que va a usar el usuario para registrarse, tomada del
                   servidor DNS

    Metodos:
        connect: Crea un socket y se conecta al servidor vega
        register(nick, password, protocol): Envia una peticion REGISTER al
                                            servidor para registrar un usuario
        query(name): Envia una peticion QUERY al servidor para averiguar la
                     address de un usuario del server dado su nombre
        list_users: Envia una peticion LIST_USERS al servidor que devuelve la
                    lista de todos los usuarios del server
        quit: Envia una peticion QUIT al servidor
    '''

    def __init__(self):
        '''
        Construye un objeto de tipo usuario y obtiene la IP del usuario
        mediante el server DNS
        '''
        self.in_call = False
        self.port = PORT

        # Obtiene la ip local
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80)) # Se conecta al servidor DNS
        self.ip = s.getsockname()[0]
        s.close()

    def connect(self):
        '''
        Crea un socket y se conecta al servidor vega
        '''
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(("vega.ii.uam.es", 8000))

    def register(self, nick, password, protocol):
        '''
        Envia una peticion REGISTER al servidor para registrar un usuario

        Parametros:
            nick (str): Nick del usuario a registar, le llega por la interfaz
            password (str): Password del usuario, le llega por la interfaz
            protocol (str): Protocolo de la practica, le llega por la interfaz

        Returns:
            False: Si el usuario ya estaba registrado en el servidor vega
            True: Si el usuario se ha registrado correctamente
        '''
        self.connect()
        message = "REGISTER {} {} {} {} {}".format(
            nick, self.ip, self.port, password, protocol)
        self.sock.send(message.encode())

        response = (self.sock.recv(MAX_STR)).decode()

        self.sock.close()
        if response == "NOK WRONG_PASS":
            print("ERROR - Usuario ya registrado\n")
            return False
        else:
            print("OK - Usuario registrado correctamente " +
                  response.split(" ")[2])
            self.nick = nick
            self.protocol = protocol
            return True

    def query(self, name):
        '''
        Envia una peticion QUERY al servidor para averiguar la address de un
        usuario del server dado su nombre

        Parametros:
            name (str): Usuario del que queremos saber su address

        Returns:
            None: Si el usuario no esta en el servidor
            user_info (tuple): tupla con IP y puerto si se ha encontrado el user
        '''
        self.connect()
        message = "QUERY " + name
        self.sock.send(message.encode())

        response = (self.sock.recv(MAX_STR)).decode()

        self.sock.close()
        if response == "NOK USER_UNKNOWN":
            print("ERROR - Usuario no encontrado")
            return None
        else:
            response_split = response.split(' ')
            user_info = (response_split[3], int(response_split[4]))
            print("OK - Usuario encontrado con IP y puerto:" + str(user_info))
            return user_info

    def list_users(self):
        '''
        Envia una peticion LIST_USERS al servidor que devuelve la lista de todos
        los usuarios del server

        Returns:
            None: Si la lista de usuarios del servidor esta vacia
            users (list): Lista de usuarios del servidor, 1 en cada posicion
        '''
        self.connect()
        message = "LIST_USERS"
        self.sock.send(message.encode())

        response_init = self.sock.recv(MAX_STR).decode()

        if response_init == "NOK USER_UNKNOWN":
            print("ERROR - No hay usuarios")
            self.sock.close()
            return None
        else:
            print("OK - Usuarios encontrados")

            # quita la parte de OK LIST_USERS de la respuesta,
            # para poner bien el primer usuario
            response = response_init[14:]

            # Coge el nº de usuarios que viene en la respuesta
            number_index = response.find(" ")
            number_of_users_total = int(response[:number_index])

            # Hace split de el resto de la respuesta, ya que cada ausuario esta
            # separado por un #
            response = response[number_index+1:]
            users = response.split("#")

            # Si la respuesta es muy larga, se enviaran varias peticiones y
            # hacemos un bucle para que lea de verdad todos los usuarios
            while len(users) < number_of_users_total:
                response_plus = self.sock.recv(MAX_STR).decode()
                response += response_plus
                users = response.split("#")

            return users[:-1]

    def quit(self):
        '''
        Envia una peticion QUIT al servidor
        '''
        self.connect()
        message = "QUIT"
        self.sock.send(message.encode())

        response = (self.sock.recv(MAX_STR)).decode()

        self.sock.close()
