#include "../includes/serverlib.h"

int main(int argc, char *argv[])
{
    int sockval, client_sock, read_size;
    struct sockaddr_in Direccion;
    char mensaje_enviado[MAX_STR] = "Mensaje escrito en el cliente";
    char mensaje_recibido[MAX_STR];

    openlog("HTTP Client", LOG_PID | LOG_NDELAY | LOG_CONS | LOG_PERROR, LOG_USER);

    /* Creación de socket */

    syslog(LOG_INFO, "Creando socket...");
    if((sockval = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
        syslog(LOG_ERR, "Error creando socket");
        exit(EXIT_FAILURE);
    }
    syslog(LOG_INFO, "Socket creado");

    Direccion.sin_family = AF_INET;
    Direccion.sin_port = htons(8080);
    Direccion.sin_addr.s_addr = inet_addr(IP);

    /* LLamada a connect */

    syslog(LOG_INFO, "Conectando al servidor...");
    if(connect(sockval, (struct sockaddr*)&Direccion, (socklen_t)sizeof(Direccion))<0){
        syslog(LOG_ERR, "Error conectando. %s", strerror(errno));
        exit(EXIT_FAILURE);
    }
    syslog(LOG_INFO, "Conexión realizada");

    /* Envío de mensaje */
    syslog(LOG_INFO, "Enviando mensaje inicial...");
    if(send(sockval, mensaje_enviado, strlen(mensaje_enviado), 0) < 0)
    {
        syslog(LOG_ERR, "Error al enviar mensaje.");
        close(sockval);
        exit(EXIT_FAILURE);
    }
    syslog(LOG_INFO, "Mensaje enviado");

    /* Recepción del mensaje */

    read_size = recv(sockval, mensaje_recibido, MAX_STR, 0);
    if(read_size < 0)
        syslog(LOG_ERR, "Fallo en la recepción");

    syslog(LOG_INFO, "Mensaje recibido: %s", mensaje_recibido);

    close(sockval);

    closelog();
    return(EXIT_SUCCESS);

}
