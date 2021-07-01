"""
    Fichero:
        practica3_client.py
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

from appJar import gui
from user_management import User
from video_client import VideoClient


class LoginForm(object):
    """
    Clase para la generación del formulario de login

    Métodos:
        start (): lanza el formulario
        loginCallback (button): callback para los botones del formulario
    """


    def __init__(self, user):
        """
        Constructor de la clase LoginForm

        Parámetros:
            user: usuario de tipo User
        """
        self.user = user
        self.app = gui()

        # Definición de los elementos de la gui
        self.app.addLabel(
            "title", "Cliente Multimedia P2P - Redes2 ", colspan=2)
        self.app.setSticky("w")
        self.app.setGuiPadding(10, 10)
        self.app.setTitle("Login Form")
        self.app.addLabel("nick", "Nick:", 1, 0)
        self.app.addEntry("nick", 1, 1)
        self.app.addLabel("protocol", "Protocol:", 2, 0)
        self.app.addEntry("protocol", 2, 1)
        self.app.setEntry("protocol", "V0")
        self.app.addLabel("password", "Password:", 3, 0)
        self.app.addSecretEntry("password", 3, 1)
        self.app.setSticky("we")

        # Botones asignados a un callback
        self.app.addButtons(["Login", "Exit"], self.loginCallback, colspan=2)

    def start(self):
        """
        Lanza la gui de LoginForm
        """

        self.app.go()

    def loginCallback(self, button):
        """
        Callback para los botones de LoginForm, que pueden ser Login o Exit

        Parámetros:
            button (str): String con el nombre del botón
        """
        if button == "Login":
            nick = self.app.getEntry("nick")
            protocol = self.app.getEntry("protocol")
            password = self.app.getEntry("password")

            if "" in [nick, protocol, password, self.user.port]:
                self.app.errorBox("Empty field", "No field can be empty")

            else:
                try:
                    register = self.user.register(nick, password, protocol)
                    if not register:
                        self.app.errorBox(
                            "Login failed", "Your credentials are invalid.")
                    else:
                        # si el usuario se autentifica lanzamos la aplicación
                        self.app.infoBox("Login successful",
                                         "You are logged in.")
                        self.app.stop() # solo puede haber una gui activa
                        vc = VideoClient("500x300", self.user)
                        vc.start()
                except:
                    self.app.errorBox("No connection", "Server is offline")
        elif button == "Exit":
            self.app.stop()


if __name__ == '__main__':
    user = User() # inicializamos el user
    lf = LoginForm(user) # inicializamos el formulario 
    lf.start() # lanzamos el formulario
