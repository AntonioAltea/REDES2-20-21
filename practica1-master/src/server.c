/**
 * Fichero principal del servidor, para la lectura del fichero de configuración,
 * cración de threads
 * 
 * @file server.c
 * @defgroup Server
 * @author Antonio Altea Segovia y Raul Cuesta Barroso
 * @date 21-5-2021
 */

#include "../includes/serverlib.h"

/**
 * Función principal del programa
 * 
 * @ingroup Server
 * @param argc Número de argumentos de la función
 * @param argv Lista de argumentos de la función
 * @return EXIT_SUCCESS si todo es correcto, EXIT_FAILURE si error
 */

int main(int argc, char *argv[])
{
    int sockval, socketDesc, client_sock, arg, num_threads = 0;
    struct sockaddr_in Direccion;
    struct sockaddr Conexion;
    struct ConfigArgs *configargs = NULL;
    pthread_t thread_id;

    FILE *config_file = NULL;
    char line[WORD_SIZE] = "";
    char config_name[WORD_SIZE] = "";
    char config_value[WORD_SIZE] = "";
    char *toks = NULL;
    char *toks_prev = NULL;

    openlog("HTTP Server", LOG_PID | LOG_NDELAY | LOG_CONS | LOG_PERROR, LOG_USER);

    /* Fichero de configuración */
    configargs = read_config_file();
    if (configargs == NULL)
    {
        syslog(LOG_ERR, "Error leyendo fichero de configuración");
        exit(EXIT_FAILURE);
    }

    /* Ignoramos SIGPIPE porque al actualizar mucho la página envia esta señal y se cerraba el servidor,
       Al ignorarla no ocurre ningún otro error y se soluciona nuestro problema. */
    sigaction(SIGPIPE, &(struct sigaction){SIG_IGN}, NULL);

    /* Funcion que crea el socket y llama a bind y listen */
    if ((sockval = start_server(configargs)) < 0)
    {
        exit(EXIT_FAILURE);
    }

    /* Llamada a accept */

    int len = sizeof(Conexion);

    while (1)
    {
        syslog(LOG_INFO, "Aceptando conexiones...");
        if ((socketDesc = accept(sockval, (struct sockaddr *)&Conexion, (socklen_t *)&len)) < 0)
        {
            syslog(LOG_ERR, "Error aceptando conexión");
            exit(EXIT_FAILURE);
        }

        configargs->socketDesc = socketDesc;

        pthread_create(&thread_id, NULL, &task, (void *)configargs);

        pthread_join(thread_id, NULL);
    }

    close(socketDesc);
    close(sockval);

    closelog();
    return (EXIT_SUCCESS);
}
