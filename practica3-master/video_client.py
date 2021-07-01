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


from appJar import gui
import control_management as cm
import call_screen
import threading

class VideoClient(object):

    """
    Clase para la interfaz del menú principal de la aplicación

    Atributos:
        window_size (str): tamaño de la ventana principal
        user (User): usuario autenticado

    Métodos:
        start (): lanza la gui
        buttonsCallback (button): callback para los botones principales
        userListCallbacks (button): callback para los botones de la lista de
                                    usuarios
        response_end (): funcion que finaliza una llamada y esconde la ventana
    """

    def __init__(self, window_size, user):
        """
        Constructor de la clase VideoClient

        Parámetros:
            window_size (str): tamaño de la ventana principal
            user (User): usuario autenticado
        """
        
        self.user = user    # usuario de la aplicación
        self.app_running = True # la aplicación está corriendo 
        self.app = gui("Redes2 - P2P", window_size)
        self.app.setGuiPadding(10, 10)
        self.tm = ""    # almacena el nombre de la ventana de llamadas
        self.streaming = False  # transmitiendo video
        self.cap = None # último frame transmitido
        self.call_stopped = False # la llamada no se ha parado

        # Preparación del interfaz
        self.app.addLabel(
            "title", self.user.nick)
        self.app.addButtons(
            ["Connect", "List Users", "Quit"], self.buttonsCallback)
        
        # Preparación de la subventana de llamadas
        with self.app.subWindow("userList", modal=True):
            self.app.addListBox("userList", [])
            self.app.addButtons(["Call", "Cancel"], self.userListCallbacks)


    def start(self):
        # creación del thread escuchador de peticiones de control
        thread_listening = threading.Thread(target=cm.listening, daemon=True, args=(self,))
        thread_listening.start()
        self.app.go()


    def buttonsCallback(self, button):

        """
        Función de callback para los botones 'principales de la interfaz

        Parámetros:
            button (str): String con el nombre del botón a gestionar. Puede ser
                          Quit, Connect o List Users
        """

        if button == "Quit":
            self.user.quit() # manda la petición de QUIT al servidor
            self.app_running = False
            self.app.stop() # detiene la aplicación

        elif button == "Connect":
            nick = self.app.textBox(
                "Conection", "Enter the nick of the user to search")
            if nick == None:
                return

            dest_addr = self.user.query(nick) # petición de información del usuario
            if dest_addr == None:
                self.app.errorBox("User not found", "User not found. Check the user list.")
                return
            
            # llamamos al usuario 
            calling_response = cm.calling(self.user.nick, self.user.port, dest_addr)
            if calling_response == "CALL_ACCEPTED":
                self.in_call = True
                # si acepta la llamada iniciamos la pantalla de llamadas
                cs = call_screen.CallScreen(self, "640x520", dest_addr, nick)
                cs.start()
            elif calling_response == "CALL_DENIED":
                self.app.errorBox("Call denied", "Call denied by " + nick)
            else:
                self.app.errorBox("Call denied", nick + " is busy")

        elif button == "List Users":
            users = self.user.list_users() # solicitamos la lista de usarios
            if users == None:
                self.app.errorBox("User list is empty", "User list is empty")
                return
            nick_list = []
            for user_nick in users:
                nick_list.append(user_nick.split(" ")[0]) # optenemos los nombres

            self.app.addListItems("userList", nick_list)
            self.app.showSubWindow("userList")


    def userListCallbacks(self, button):
        """
        Función de callback para los botones de la lista de usuarios

        Parámetros:
            button (str): String con el nombre del botón a gestionar. Puede ser
                          Call o Cancel
        """
        if button == "Cancel":
            self.app.hideSubWindow("userList")
        else:
            # obtenemos el usuario seleccionado
            selected_nick = self.app.getListBox("userList")[0]
            if selected_nick != None:
                dest_addr = self.user.query(selected_nick) # preguntamos su información
                if dest_addr == None:
                    self.app.errorBox("User not found", "User not found. Check the user list.")
                    return

                # llamamos al usuario
                calling_response = cm.calling(self.user.nick, self.user.port, dest_addr)
                self.app.hideSubWindow("userList") # escondemos la lista
                if calling_response == "CALL_ACCEPTED":
                    # si acepta la llamada iniciamos la pantalla de llamada
                    cs = call_screen.CallScreen(self, "640x520", dest_addr, selected_nick)
                    cs.start()
                elif calling_response == "CALL_DENIED":
                    self.app.errorBox("Call denied", "Call denied by " + selected_nick)
                else:
                    self.app.errorBox("Call denied", selected_nick + " is busy")


    def response_end(self):
        """
        Función para finalizar una llamada y esconder la ventana de esta

        """
        self.app.removeStatusbar()
        self.in_call = False
        self.streaming = False
        self.cap.release()
        self.app.hideSubWindow(self.tm)
