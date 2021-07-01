"""
    Fichero:
        control_management.py
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
import call_screen

MAX_STR = 2048 # Tam maximo para recibir las respuestas
CONTROL_PORT = 4000 # Puerto que usamos para recibir las señales P2P de control,
                    # que es diferente al que usamos para transmitir la webcam

def calling(my_nick: str, my_UDPport: int, dest_address: tuple) -> int:
    """
    Envia una señal CALLING a otro usuario indicando que quiere hacer una
    videollamada con el mismo

    Parametros:
        my_nick (str): nick de la persona que llama
        my_UDPport (int): puerto UDP en el que el llamante desea recibir el
                          video del llamado
        dest_address (tuple): tupla con IP y puerto de la persona a la
                              que queremos llamar, sale de una query al server

    Returns:
        CALL_ACCEPTED (str): si la respuesta que recibe después del calling
                             contiene (es) "CALL_ACCEPTED"
        CALL_DENIED (str): si la respuesta contiene "CALL_DENIED"
        CALL_BUSY (str): si la respuesta contiene "CALL_BUSY"

    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Se intenta conectar con el usuario. Si el otro usuario no contesta
    # en 5 segundos, devuelve CALL_DENIED
    sock.settimeout(5)
    try:
        print((dest_address[0], CONTROL_PORT))
        sock.connect((dest_address[0], CONTROL_PORT))
    except:
        return "CALL_DENIED"
    sock.settimeout(None)

    # Le envia la peticion CALLING a su address
    message = "CALLING {} {}".format(my_nick, my_UDPport)
    sock.send(message.encode())

    # Procesa la respuesta
    response = (sock.recv(MAX_STR)).decode()
    sock.close()
    if "CALL_ACCEPTED" in response:
        return "CALL_ACCEPTED"
    elif "CALL_DENIED" in response:
        return "CALL_DENIED"
    else:  # CALL_BUSY
        return "CALL_BUSY"

def call_hold(src_nick: str, dest_address: tuple):
    """
    Envia una señal de tipo CALL_HOLD a un usuario. Señaliza que se desea
    pausar temporalmente la transmision de video en una llamada, sin colgar.

    Parametros:
        src_nick (str): nick de la persona que quiere pausar la llamada
        dest_address (tuple): tupla con IP y puerto de la persona a la
                              que queremos enviar la peticion CALL_HOLD
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((dest_address[0], CONTROL_PORT))

    message = "CALL_HOLD " + src_nick
    sock.send(message.encode())

    sock.close()
    # No espera respuesta

def call_resume(src_nick: str, dest_address: tuple):
    """
    Envia una señal de tipo CALL_RESUME a un usuario. Señaliza que se desea
    reanudar una llamada anteriormente pausada por una señal CALL_HOLD.

    Parametros:
        src_nick (str): nick de la persona que quiere reanudar la llamada
        dest_address (tuple): tupla con IP y puerto de la persona a la
                              que queremos enviar la peticion CALL_RESUME
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((dest_address[0], CONTROL_PORT))

    message = "CALL_RESUME " + src_nick
    sock.send(message.encode())

    sock.close()
    # No espera respuesta

def call_end(src_nick: str, dest_address: tuple):
    """
    Envia una señal de tipo CALL_END a un usuario. Señaliza que se desea
    finalizar una llamada en curso.

    Parametros:
        src_nick (str): nick de la persona que quiere reanudar la llamada
        dest_address (tuple): tupla con IP y puerto de la persona a la
                              que queremos enviar la peticion CALL_END
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((dest_address[0], CONTROL_PORT))

    message = "CALL_END " + src_nick
    sock.send(message.encode())

    sock.close()
    # No espera respuesta

def listening(video_client):
    """
    Funcion realiza por un thread, que esta a la escucha de posibles señales
    de control que le puedan llegar (CALLING, CALL_HOLD...). Dependiendo de cual
    reciba, hace varias acciones que afectan a la interfaz.

    Parametros:
        video_client (object): interfaz de la aplicacion principal
    """

    # Se abre el puerto de control para escuchar
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    my_address = (video_client.user.ip, CONTROL_PORT)
    sock.bind(my_address)
    sock.listen(1)

    # Mientras que no se pulse el boton de Quit en video_client para actualizar
    # la condicion, el hilo sigue escuchando en el socket de control
    while video_client.app_running:

        # Recibe la respuesta
        connection, their_address = sock.accept()
        response = connection.recvfrom(MAX_STR)
        response = response[0].decode()

        # Procesa la respuesta
        if "CALLING" in response:
            response_split = response.split(" ")
            their_nick = response_split[1]
            their_port = int(response_split[2])

            # Si el usuario esta en llamda, envia de vuelta el mensaje CALL_BUSY
            # si no esta en llamada, aparece una ventana donde se elige si
            # aceptar o rechazar la llamada.
            if video_client.user.in_call == False:
                accept_box = video_client.app.yesNoBox("entering_call", "Entering call from " + their_nick)
                if accept_box:
                    message = "CALL_ACCEPTED {} {}".format(video_client.user.nick, video_client.user.port)
                    connection.send(message.encode())

                    #En caso de aceptar la llamada se crea la intefaz de call_screen
                    video_client.user.in_call == True
                    cs = call_screen.CallScreen(video_client, "640x520", (their_address[0], their_port), their_nick)
                    cs.start()
                else:
                    message = "CALL_DENIED " + video_client.user.nick
                    connection.send(message.encode())
            else:
                message = "CALL_BUSY "
                connection.send(message.encode())

        elif "CALL_HOLD" in response:
            video_client.call_stopped = True

        elif "CALL_RESUME" in response:
            video_client.call_stopped = False

        elif "CALL_END" in response:
            video_client.response_end()

        connection.close()

    sock.close()
