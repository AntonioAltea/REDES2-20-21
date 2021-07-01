"""
    Fichero:
        video_client.py
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
import cv2
import control_management as cm
import threading
from PIL import Image, ImageTk
from datetime import datetime
import time
import numpy as np

class CallScreen(object):

    """
    Clase para la interfaz de la subventana de llamadas

    Atributos:
        video_client (VideoClient): instancia de la interfaz padre 
        dest_addr (tuple(str, int)): tupla con la dirección del interlocutor
        dest_nick (str): nick del interlocutor

    Métodos:
        start (): lanza la gui
        buttonsCallback (button): callback para los botones principales
        send_video(): función que captura la cámara y enviará vídeo al interloculor
        receive_video() : función que recive vídeo y actualiza la interfaz
        setImageREsolution (): funcion que cambia la calidad con que se captura
                               la imágen de la cámara
    """

    def __init__(self, video_client, window_size, dest_addr, dest_nick):
        """
        Constructor de la clase CallScreen

        Parámetros:
            video_client (VideoClient): instancia de la interfaz padre 
            dest_addr (tuple(str, int)): tupla con la dirección del interlocutor
            dest_nick (str): nick del interlocutor
        """

        self.user = video_client.user # usuario autenticado dle sistema
        self.dest_addr = dest_addr 
        self.dest_nick = dest_nick
        self.video_client = video_client
        self.video_client.streaming = True # notifica streaming a True
        self.app = video_client.app
        self.encimg = None # aquí guardaremos el frame enviado
        self.width = 320
        self.height = 240
        self.fps = 30

        self.video_client.tm = str(datetime.now()) # nombre de la ventana

        self.app.startSubWindow(self.video_client.tm, modal=True)

        # Preparación del interfaz
        try:
            self.app.addLabel("call_title", dest_nick)
            self.app.addImage("video", "imgs/webcam.gif")
            self.app.addLabel("mynick", self.user.nick)
            self.app.addImage("video_propio", "imgs/webcam.gif")
            self.app.addButtons(
                ["Stop/Resume Call", "Exit Call"], self.buttonsCallback)
            self.app.addStatusbar(fields=2)
        except:
            # si ya han sido creados los eliminamos y los volvemos añadir
            self.app.removeLabel("call_title")
            self.app.removeImage("video")
            self.app.removeLabel("mynick")
            self.app.removeImage("video_propio")
            self.app.removeButton("Stop/Resume Call")
            self.app.removeButton("Exit Call")
            self.app.removeStatusbar()

            self.app.addLabel("call_title", dest_nick)
            self.app.addImage("video", "imgs/webcam.gif")

            self.app.addLabel("mynick", self.user.nick)
            self.app.addImage("video_propio", "imgs/webcam.gif")
            self.app.addButtons(
                ["Stop/Resume Call", "Exit Call"], self.buttonsCallback)
            self.app.addStatusbar(fields=2)

        self.app.setImageSize("video", 320, 240)
        self.app.setImageSize("video_propio", 320, 240)
        

        # Registramos la función de captura de video
        self.video_client.cap = cv2.VideoCapture(0)
        self.app.setPollTime(20)
        self.setImageResolution("HIGH")

    def start(self):
        """
        Función que comienza la ventana y los hilos
        """

        self.app.showSubWindow(self.video_client.tm)
        # inicializa envío y recepción de video en sus propios hilos
        thread_send_video = threading.Thread(target=self.send_video, daemon=False)
        thread_receive_video = threading.Thread(target=self.receive_video, daemon=False)
        thread_send_video.start()
        thread_receive_video.start()


    # Función que gestiona los callbacks de los botones
    def buttonsCallback(self, button):

        """
        Función de callback para los botones 'principales de la interfaz

        Parámetros:
            button (str): String con el nombre del botón a gestionar. Puede ser
                          Stop/Resume Call, Exit Call
        """

        if button == "Exit Call":
            # notificamos el fin de la llamada
            cm.call_end(self.user.nick, self.dest_addr)
            self.app.removeStatusbar()
            # detiene la captura de imágenes
            self.video_client.cap.release()
            self.app.hideSubWindow(self.video_client.tm)
            self.app.stopSubWindow()
            self.video_client.streaming = False

        if button == "Stop/Resume Call":
            if self.video_client.call_stopped:
                # petición de continuación
                cm.call_resume(self.user.nick, self.dest_addr)
                self.video_client.call_stopped = False

            else:
                # petición de parada
                cm.call_hold(self.user.nick, self.dest_addr)
                self.video_client.call_stopped = True


    def send_video(self):
        """
        Función encargada de capturar imágenes de la cámara, comprimirlas,
        codificarlas y enviarlas al interlocutor.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        number = 1
        while self.video_client.streaming:
            if not self.video_client.call_stopped:
                # Timing de frames
                time.sleep(1/self.fps)

                try:
                    # Capturamos un frame de la cámara o del vídeo
                    ret, img = self.video_client.cap.read()

                    self.encimg = img

                    # Compresión JPG al 50% de resolución
                    encode_param = [cv2.IMWRITE_JPEG_QUALITY,50]
                    result, encimg = cv2.imencode('.jpg', img,encode_param)
                    if result == False:
                        print('Error al codificar imagen')
                    encimg = encimg.tobytes()
                    # Los datos "encimg" ya están listos para su envío por la red y se envian

                    # Creamos el mensaje con las cabeceras correspondientes
                    message = str(number) + '#' + str(time.time()) + '#' + "{}x{}".format(self.width, self.height) + '#' + str(self.fps) + '#'
                    message = message.encode() + encimg
                    sock.sendto(message,self.dest_addr) # envío del mensaje
                    number += 1
                except:
                    pass
        sock.close()

    def receive_video(self):
        """
        Función encargada de recivir imágenes del interloculos y mostrarlas por
        la interfaz junto con las propias.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        my_address = (self.user.ip, self.user.port)
        sock.bind(my_address)
        
        time.sleep(0.5)

        while self.video_client.streaming:
            if not self.video_client.call_stopped:
                buffer, addr = sock.recvfrom(600000)

                fields = buffer.split(b'#') # separamos los valores de la cabecera
                frame_number = fields[0].decode()
                timestamp = fields[1].decode()
                resolution = fields[2].decode()
                fps = fields[3].decode()

                # volvemos a unir la imágene que se separó por el split
                img = b'#'.join(fields[4:])

                #a ctualizamos la barra de estado
                self.app.setStatusbar("FPS: {}".format(fps), field=0)
                self.app.setStatusbar("resolution: {}".format(resolution), field=1)
                
                # Descompresión de los datos, una vez recibidos
                dec_img = cv2.imdecode(np.frombuffer(img, np.uint8), 1)

                # Conversión de formato para su uso en el GUI
                try:
                    frame_base = cv2.resize(dec_img, (self.width,self.height))
                    frame_peque = cv2.resize(self.encimg, (self.width,self.height))

                    cv2_im = cv2.cvtColor(frame_base, cv2.COLOR_BGR2RGB)
                    img_tk = ImageTk.PhotoImage(Image.fromarray(cv2_im))
                    self.app.setImageData("video", img_tk, fmt="PhotoImage")

                    cv2_im = cv2.cvtColor(frame_peque, cv2.COLOR_BGR2RGB)
                    img_tk = ImageTk.PhotoImage(Image.fromarray(cv2_im))

                    self.app.setImageData("video_propio", img_tk, fmt="PhotoImage")
                except:
                    pass
        sock.close()

    def setImageResolution(self, resolution):
        """
        Establece la resolución de la imagen capturada

        Parámetros:
            resolution (str): Puede ser LOW, MEDIUM o HIGH
        
        """
        if resolution == "LOW":
            self.video_client.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 160)
            self.video_client.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 120)
        elif resolution == "MEDIUM":
            self.video_client.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
            self.video_client.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
        elif resolution == "HIGH":
            self.video_client.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.video_client.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
