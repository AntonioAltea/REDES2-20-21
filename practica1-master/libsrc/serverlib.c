/**
 * @brief Librería de server
 *
 * Aquí se define la funcionalidad del servidor para el proceso de
 * peticiones http
 *
 * @file serverlib.c
 * @author Antonio Altea Segovia y Raul Cuesta Barroso
 * @date 21-5-2021
 */

#include "../includes/serverlib.h"
#include "../includes/picohttpparser.h"


/**
* @brief ConfigArgs* read_config_file();
*
* Lee el fichero de configuracion del servidor y crea y rellena
* los campos de una estructura donde guarda esa configuracion.
*
* @ingroup Serverlib
* @return ConfigArgs* - Puntero a la estructura ConfigArgs creada y rellenada.
*/
struct ConfigArgs *read_config_file()
{
    FILE *config_file = NULL;
    char line[WORD_SIZE] = "";
    char config_name[WORD_SIZE] = "";
    char config_value[WORD_SIZE] = "";
    char *toks = NULL;
    char *toks_prev = NULL;
    struct ConfigArgs *configargs;

    configargs = malloc(sizeof(struct ConfigArgs));
    if (configargs == NULL)
    {
        return NULL;
    }

    config_file = fopen(CONFIG_NAME, "r");
    if (config_file == NULL)
    {
        syslog(LOG_ERR, "Debe existir un file_str 'server.conf' al lado del ejecutable");
        exit(EXIT_FAILURE);
    }

    fseek(config_file, 0, SEEK_SET);

    while (fgets(line, WORD_SIZE, config_file))
    {
        if (strncmp("#", line, 1) != 0) /* si no es comentario */
        {
            toks = strtok(line, " = ");
            strcpy(config_name, toks);
            toks = strtok(NULL, " ");
            toks = strtok(NULL, "\n\0");
            strcpy(config_value, toks);

            if (strcmp(config_name, "server_root") == 0)
            {
                strcpy(configargs->server_root, config_value);
            }
            else if (strcmp(config_name, "max_clients") == 0)
            {
                configargs->max_clients = atol(config_value);
            }
            else if (strcmp(config_name, "listen_port") == 0)
            {
                configargs->port = atol(config_value);
            }
            else if (strcmp(config_name, "server_signature") == 0)
            {
                strcpy(configargs->server_signature, config_value);
            }
            else
            {
                syslog(LOG_INFO, "El parametro de configuracion '%s' no esta implementado", config_name);
                return NULL;
            }
        }
    }

    fclose(config_file);

    return configargs;
}


/**
* @brief int start_server(struct ConfigArgs* args)
*
* Iniciando el servidor mediante varias llamadas. Primero crea el socket con socket() y
* luego con el valor de retorno llama a bind() y listen().
*
* @ingroup Serverlib
* @param args Puntero a una estructura ConfigArgs que contiene la configuracion del servidor.
* @return Entero con el valor de retorno de socket(...) o -1 en caso de error.
*/
int start_server(struct ConfigArgs *args)
{
    int sockval;
    struct sockaddr_in Direction;

    /* Creación de socket */
    syslog(LOG_INFO, "Creando socket...");
    if ((sockval = socket(AF_INET, SOCK_STREAM, 0)) < 0)
    {
        syslog(LOG_ERR, "Error creando socket");
        return -1;
    }

    Direction.sin_family = AF_INET;
    Direction.sin_port = htons(args->port);
    Direction.sin_addr.s_addr = INADDR_ANY;

    if (setsockopt(sockval, SOL_SOCKET, SO_REUSEADDR, &(int){1}, sizeof(int)) < 0)
        syslog(LOG_ERR, "setsockopt(SO_REUSEADDR) failed");

    /* LLamada a bind */
    syslog(LOG_INFO, "Binding del socket...");
    if (bind(sockval, (struct sockaddr *)&Direction, (socklen_t)sizeof(Direction)) < 0)
    {
        syslog(LOG_ERR, "Error en binding");
        return -1;
    }

    /* Lamada a listen */
    syslog(LOG_INFO, "Comenzando escucha de conexiones...");
    if (listen(sockval, args->max_clients) < 0)
    {
        syslog(LOG_ERR, "Error de listen");
        return -1;
    }

    return sockval;
}


/**
* @brief void* task(void* args)
*
* Parsea una peticion HTTP, guardando su informacion, y llama al metodo GET, POST o OPTIONS. Es ejecutada por un thread.
*
* @ingroup Serverlib
* @param args Puntero a una estructura que contiene la configuracion del servidor.
* @return NULL en cualquier caso, si ha habido un error se plasma en forma de respuesta HTTP y no como un return.
*/
void *task(void *args)
{
    /* Variables de picohttpparser */
    int pret, minor_version, i;
    char message[MAX_STR];
    char body[MAX_STR];
    const char *method, *path;
    char method_str[MAX_STR], path_str[MAX_STR];
    char response[MAX_STR * 4];
    size_t read_size, method_len, path_len, num_headers, prevbuflen = 0, buflen = 0;
    struct ConfigArgs *arguments = (struct ConfigArgs *)args;
    struct phr_header headers[100];

    char *file_str = (char *)malloc(sizeof(char) * MAX_STR + 1);

    /* Páginas de error */
    char bad_request_message[MAX_STR] = "<html><head>\n<title>400 Bad Request</title>\n</head><body>\n<h1>Bad Request</h1>\nServer couldn't parse the request.\n</body></html>";
    char too_long_message[MAX_STR] = "<html><head>\n<title>414 Request URI too long</title>\n</head><body>\n<h1>Request URI too long</h1>\nServer couldn't parse the request.\n</body></html>";
    /* Variables de tiempo */
    char *time_buf, *last_mod_buf;

    /* Limpiamos las variables */
    memset(message, 0, sizeof(message));
    memset(method_str, 0, sizeof(method_str));

    /* Cálculo del tiempo actual */
    time_buf = real_time();

    while (1) /* bucle para leer la peticion */
    {

        while ((read_size = read(arguments->socketDesc, message + buflen, sizeof(message) - buflen)) == -1 && errno == EINTR)
            ;
        if (read_size < 0)
        {
            syslog(LOG_ERR, "Fallo en la recepcion");
            return NULL;
        }
        prevbuflen = buflen;
        buflen += read_size;
        num_headers = sizeof(headers) / sizeof(headers[0]);

        pret = 0;
        pret = phr_parse_request(message, read_size, &method, &method_len, &path, &path_len, &minor_version, headers, &num_headers, prevbuflen);
        if (pret != 0)
        {
            if (pret > 0)
            { /* sale si acaba de mirar todos los headers y no hay errores */
                break;
            }
            else if (pret == -1)
            {
                sprintf(response, "HTTP/1.1 400 Bad Request\r\nDate: %s\r\nServer: %s\r\nContent-Length: %ld\r\n"
                                  "Connection: close\r\nContent-Type: text/html\r\n\r\n%s",
                        time_buf, arguments->server_signature, sizeof(bad_request_message), bad_request_message);
                (void)write(arguments->socketDesc, response, sizeof(response));
                syslog(LOG_INFO, "400 Bad Request");
                close(arguments->socketDesc);
                return NULL;
            }
            assert(pret == -2);
            if (buflen == sizeof(message))
            {
                sprintf(response, "HTTP/1.1 414 Request URI too long\r\nDate: %s\r\nServer: %s\r\nContent-Length: %ld\r\n"
                                  "Connection: close\r\nContent-Type: text/html\r\n%s",
                        time_buf, arguments->server_signature, sizeof(too_long_message), too_long_message);
                (void)write(arguments->socketDesc, response, sizeof(response));
                syslog(LOG_INFO, "414 Request URI too long");
                close(arguments->socketDesc);
                return NULL;
            }
            break;
        }
    }

    /* Almacenamos el método en method_str */
    if (path_len == 1)
    {
        path = "index.html";
        path_len = strlen("index.html");
    }
    strncpy(method_str, method, method_len);
    sprintf(path_str, "%.*s", (int)path_len, path);

    if (!strcmp(method_str, "OPTIONS"))
    {
        manage_options(time_buf, arguments);
    }
    else if (!strcmp(method_str, "GET"))
    {
        manage_get(time_buf, path_str, arguments);
    }
    else if (!strcmp(method_str, "POST"))
    {
        sprintf(body, "%s", message + pret);
        manage_post(time_buf, path_str, arguments, body);
    }
    else
    {
        not_supported_verb(time_buf, arguments);
    }
    return NULL;
}


/**
* @brief void manage_get(char *time_buf, char *path_str, struct ConfigArgs *configarguments)
*
* Realiza las acciones necesarias al recibir una peticion con el metodo GET en task(...). Esto incluye manejar
* los argumentos de la URL y entregar el fichero o ejecutar un script.
*
* @ingroup Serverlib
* @param time_buf string que contiene la fecha y hora formateada en la que el servidor a recibido la conexion que se esta tratando.
* @param path_str string que contiene el path parseado en task(...).
* @param configarguments puntero a una estructura con la configuracion del servidor.
* @return Nada, en caso de error llama a las funciones necesarias que envian la peticion HTTP con el error correspondiente.
*/
void manage_get(char *time_buf, char *path_str, struct ConfigArgs *configarguments)
{

    char *url_arguments;
    char *file_str = (char *)malloc(sizeof(char) * MAX_STR / 4);
    char *arg;
    char arguments[MAX_STR / 4] = "";
    char path_str_args[MAX_STR/4];
    int n_args = 0;

    strcpy(path_str_args, path_str);

    if ((url_arguments = strstr(path_str, "?")) == NULL)
    { /* no tiene arguementos */

        sprintf(file_str, "%s%s", configarguments->server_root, path_str);
    }
    else
    {
        /* quita ? de url_arguments */
        memmove(url_arguments, url_arguments + 1, strlen(url_arguments));
        arg = strtok(url_arguments, "&");
        while (arg != NULL)
        {
            strcat(arguments, arg);
            strcat(arguments, " ");

            arg = strtok(NULL, "&");
        }

        sprintf(file_str, "%s%s", configarguments->server_root, strtok(path_str_args, "?"));
    }

    if (access(file_str, F_OK) == 0)
    {
        if (!strcmp(get_file_extension(file_str), "py") || !strcmp(get_file_extension(file_str), "php"))
        {
            if (exe_script(time_buf, file_str, arguments, configarguments) == -1) {
                syslog(LOG_ERR,"Error al ejecutar el script en respuesta GET");
            }
        }
        else
        {
            serve_file(file_str, time_buf, configarguments);
        }
    }
    else
    { /* si el file_str no existe */
        file_doesnt_exist(time_buf, configarguments);
    }
}


/**
* @brief void manage_post(char *time_buf, char *path_str, struct ConfigArgs *configarguments)
*
* Realiza las acciones necesarias al recibir una peticion con el metodo POST en task(...). Esto incluye manejar
* los argumentos del cuerpo y modificar el fichero o ejecutar un script.
*
* @ingroup Serverlib
* @param time_buf string que contiene la fecha y hora formateada en la que el servidor a recibido la conexion que se esta tratando.
* @param path_str string que contiene el path parseado en task(...).
* @param configarguments puntero a una estructura con la configuracion del servidor.
* @param body cuerpo de la request donde estan los argumentos que puede usar POST.
* @return Nada, en caso de error llama a las funciones necesarias que envian la peticion HTTP con el error correspondiente.
*/
void manage_post(char *time_buf, char *path_str, struct ConfigArgs *configarguments, char *body)
{
    char *url_arguments;
    char *file_str = (char *)malloc(sizeof(char) * MAX_STR / 4);
    char *arg;
    char arguments[MAX_STR / 4] = "";
    char path_str_args[MAX_STR/4];
    int n_args = 0;
    int args_body = 0; /* 0 indica que estan el la URL, 1 en el cuerpo */
    char response[MAX_STR * 4];

    strcpy(path_str_args, path_str);

    if ((url_arguments = strstr(path_str, "?")) == NULL)
    { /* no tiene argumentos en la URL luego estan en el cuerpo */
        sprintf(file_str, "%s%s", configarguments->server_root, path_str);
        args_body = 1;
    }
    else
    {
        /* quita ? de url_arguments */
        memmove(url_arguments, url_arguments + 1, strlen(url_arguments));
        arg = strtok(url_arguments, "&");
        while (arg != NULL)
        {
            strcat(arguments, arg);
            strcat(arguments, " ");

            arg = strtok(NULL, "&");
        }

        sprintf(file_str, "%s%s", configarguments->server_root, strtok(path_str_args, "?"));
    }

    if (access(file_str, F_OK) == 0)
    {
        if (!strcmp(get_file_extension(file_str), "py") || !strcmp(get_file_extension(file_str), "php"))
        {
            if (args_body == 1) { /* argumentos en el cuerpo */
                if (exe_script(time_buf, file_str, body, configarguments) == -1) {
                    syslog(LOG_ERR,"Error al ejecutar el script en respuesta POST");
                }
            }
            else {
                if (exe_script(time_buf, file_str, arguments, configarguments) == -1) {
                    syslog(LOG_ERR,"Error al ejecutar el script en respuesta GET/POST");
                }
            }
        }

        sprintf(response, "HTTP/1.1 200 OK\r\nDate: %s\r\nServer: %s\r\nLast-Modified: 0\r\nContent-Length: 0\r\nConnection: close\r\n"
                          "Content-Type: %s\r\n\r\n",
                time_buf, configarguments->server_signature, body);
        (void)write(configarguments->socketDesc, response, strlen(response));
        //200 OK
    }
    else
    { /* si el file_str no existe */
        file_doesnt_exist(time_buf, configarguments);
    }
}


/**
* @brief void manage_options(char *time_buf, struct ConfigArgs *arguments)
*
* Realiza las acciones necesarias al recibir una peticion con el metodo OPTIONS en task(...). Esto consistente en
* incluir en la cabecera de la respuesta un campo "Allow" con los metodos permitidos por el servidor.
*
* @ingroup Serverlib
* @param time_buf string que contiene la fecha y hora formateada en la que el servidor a recibido la conexion que se esta tratando.
* @param path_str string que contiene el path parseado en task(...).
* @param configarguments puntero a una estructura con la configuracion del servidor.
* @return Nada, en caso de error llama a las funciones necesarias que envian la peticion HTTP con el error correspondiente.
*/
void manage_options(char *time_buf, struct ConfigArgs *arguments)
{
    char response[MAX_STR * 4];
    sprintf(response, "HTTP/1.1 200 OK\r\nDate: %s\r\nServer: %s\r\nContent-Length: 0\r\nAllow:GET,POST,OPTIONS\r\n\r\n",
            time_buf, arguments->server_signature);
    (void)write(arguments->socketDesc, response, strlen(response));
    syslog(LOG_INFO, "OPTIONS");
}


/**
* @brief serve_file(char *file_str, char *time_buf, struct ConfigArgs *arguments)
*
* En el caso de haber recibido una peticion GET y no ser un script, esta funcion permite a manage_get(...) devolver un fichero como respuesta a esa peticion.
*
* @ingroup Serverlib
* @param file_str string que contiene el path del fichero modificado en manage_get(...) segun si tenia argumentos la URL.
* @param time_buf string que contiene la fecha y hora formateada en la que el servidor a recibido la conexion que se esta tratando.
* @param configarguments puntero a una estructura con la configuracion del servidor.
* @return Nada, en caso de error llama a las funciones necesarias que envian la peticion HTTP con el error correspondiente.
*/
void serve_file(char *file_str, char *time_buf, struct ConfigArgs *arguments)
{
    char unsuported_message[MAX_STR] = "<html><head>\n<title>415 Unsuported Media Type</title>\n</head><body>\n<h1>415 Unsuported Media Type</h1>\nUnsuported Media Type.\n</body></html>";
    char *last_mod_buf;
    char response[MAX_STR * 4];
    unsigned char buffer_file_str[MAX_STR];
    struct stat fileattrib;
    /* Fecha de última modificación */
    stat(file_str, &fileattrib);
    last_mod_buf = last_mod_time(fileattrib);

    memset(buffer_file_str, 0, sizeof(buffer_file_str));

    /* escribir message */
    FILE *file_str_fd;

    if (!(file_str_fd = fopen(file_str, "rb")))
    {
        close(arguments->socketDesc);
        return;
    }

    long len;
    fseek(file_str_fd, 0, SEEK_END);
    len = ftell(file_str_fd);
    fseek(file_str_fd, 0, SEEK_SET);

    const char *content_type = get_content_type(file_str);

    if (content_type == NULL)
    {
        sprintf(response, "HTTP/1.1 415 Unsupported Media Type\r\nDate: %s\r\nServer: %s\r\nContent-Length: %ld\r\n Connection: close\r\nContent-Type: text/html\r\n\r\n%s",
                time_buf, arguments->server_signature, strlen(unsuported_message), unsuported_message);
        (void)write(arguments->socketDesc, response, strlen(response));
        syslog(LOG_INFO, "415 Unsupported Media TYpe");
    }

    sprintf(response, "HTTP/1.1 200 OK\r\nDate: %s\r\nServer: %s\r\nLast-Modified: %s\r\nContent-Length: %ld\r\nConnection: close\r\n"
                      "Content-Type: %s\r\n\r\n",
            time_buf, arguments->server_signature, last_mod_buf, len, content_type);
    (void)write(arguments->socketDesc, response, strlen(response));

    size_t bytesRead = 0;
    while ((bytesRead = fread(buffer_file_str, 1, sizeof(buffer_file_str), file_str_fd)) > 0)
    {
        if (write(arguments->socketDesc, buffer_file_str, bytesRead) < 0)
        {
            return;
        }
    }
    syslog(LOG_INFO, "200 OK");
    fclose(file_str_fd);
}


/**
* @brief exe_script(char *time_buf, char *file_str, char *arguments, struct ConfigArgs *configarguments)
*
* En el caso de haber recibido una peticion GET o POST con un fichero .py o .php que son scripts, ejecuta el script y envia la salida como respuesta HTTP.
*
* @ingroup Serverlib
* @param time_buf string que contiene la fecha y hora formateada en la que el servidor a recibido la conexion que se esta tratando.
* @param file_str string que contiene el path del fichero modificado en manage_get(...) segun si tenia argumentos la URL.
* @param arguments string que contiene los argumentos del script a ejecutar, hallados en manage_get(...) o manage_post(...).
* @param configarguments puntero a una estructura con la configuracion del servidor.
* @return 0 si se ha ejecutado correctamente el script, -1 en caso contrario.
*/
int exe_script(char *time_buf, char *file_str, char *arguments, struct ConfigArgs *configarguments)
{
    char script[MAX_STR];
    FILE *script_file;
    char script_result[MAX_STR];
    char response[MAX_STR * 4];

    char *last_mod_buf;
    struct stat fileattrib;

    stat(file_str, &fileattrib);
    last_mod_buf = last_mod_time(fileattrib);

    if (!strcmp(get_file_extension(file_str), "py"))
    {
        sprintf(script, "echo %s | python3 %s %s", arguments, file_str, arguments);
    }
    else if (!strcmp(get_file_extension(file_str), "php"))
    {
        sprintf(script, "echo %s | php %s %s", arguments, file_str, arguments);
    }

    script_file = popen(script, "r");
    if (script_file == NULL)
    {
        return -1;
    }
    fread(script_result, 1, MAX_STR, script_file);

    sprintf(response, "HTTP/1.1 200 OK\r\nDate: %s\r\nServer: %s\r\nLast-Modified: %s\r\nContent-Length: %ld\r\nConnection: close\r\n"
                      "Content-Type: text/html\r\n\r\n%s",
            time_buf, configarguments->server_signature, last_mod_buf, strlen(script_result), script_result);
    (void)write(configarguments->socketDesc, response, strlen(response));
    return 0;
}


/**
* @brief file_doesnt_exist(char *time_buf, struct ConfigArgs *arguments)
*
* Envia la respuesta HTTP de "404 Not Found". Es una funcion auxiliar para no repetir código.
*
* @ingroup Serverlib
* @param time_buf string que contiene la fecha y hora formateada en la que el servidor a recibido la conexion que se esta tratando.
* @param configarguments puntero a una estructura con la configuracion del servidor.
* @return Nada, simplemente envia la peticion HTTP con el error correspondiente.
*/
void file_doesnt_exist(char *time_buf, struct ConfigArgs *arguments)
{
    char response[MAX_STR * 4];
    char not_found_message[MAX_STR] = "<html><head>\n<title>404 Not Found</title>\n</head><body>\n<h1>404 Not Found</h1>\nFile not found.\n</body></html>";

    sprintf(response, "HTTP/1.1 404 Not Found\r\nDate: %s\r\nServer: %s\r\nContent-Length: %ld\r\nConnection: close\r\n"
                      "Content-Type: text/html\r\n\r\n%s",
            time_buf, arguments->server_signature, strlen(not_found_message), not_found_message);
    (void)write(arguments->socketDesc, response, strlen(response));
    syslog(LOG_INFO, "404 Not Found");
}


/**
* @brief not_supported_verb(char *time_buf, struct ConfigArgs *arguments)
*
* Envia la respuesta HTTP de "405 Method Not Allowed". Es una funcion auxiliar para no repetir código.
*
* @ingroup Serverlib
* @param time_buf string que contiene la fecha y hora formateada en la que el servidor a recibido la conexion que se esta tratando.
* @param configarguments puntero a una estructura con la configuracion del servidor.
* @return Nada, simplemente envia la peticion HTTP con el error correspondiente.
*/
void not_supported_verb(char *time_buf, struct ConfigArgs *arguments)
{
    char response[MAX_STR * 4];
    char method_not_allowed_message[MAX_STR] = "<html><head>\n<title>405 Method Not Allowed</title>\n</head><body>\n<h1>405 Method Not Allowed</h1>\nMethod Not Allowed.\n</body></html>";

    sprintf(response, "HTTP/1.1 405 Method Not Allowed\r\nDate: %s\r\nServer: %s\r\nContent-Length: %ld\r\nConnection: close\r\nAllow:GET,POST,OPTIONS\n\nContent-Type: text/html\r\n\r\n%s",
            time_buf, arguments->server_signature, strlen(method_not_allowed_message), method_not_allowed_message);
    (void)write(arguments->socketDesc, response, strlen(response));
    syslog(LOG_INFO, "405 Method not allowed");
}


/**
* @brief const char *get_file_extension(const char *filename)
*
* Devuelve la extension de un fichero (a partir del punto). Para ello recibe una string de entrada.
*
* @ingroup Serverlib
* @param filename Nombre de un fichero a analizar.
* @return String que contiene la extension a partir del punto en caso de que la string inicial tuviera extension, una string vacia en caso contrario.
*/
const char *get_file_extension(const char *filename)
{
    const char *dot = strrchr(filename, '.');
    if (!dot || dot == filename)
    {
        return "";
    }
    return dot + 1;
}


/**
* @brief const char *get_content_type(const char *filename)
*
* Devuelve el tipo de un fichero como string para meterlo en una cabecera HTTP. Para ello recibe una string de entrada y
* usa la funcion get_file_extension(...) para obtener la extension del fichero y con ello saber el tipo, predefinido por nosotros.
*
* @ingroup Serverlib
* @param filename Nombre de un fichero a analizar.
* @return char* - String con el tipo del fichero (definidos por nosotros acorde al enujnciado).
*         NULL - En caso de recibir un fichero con una extension y por lo tanto tipo que no soportamos.
*/
const char *get_content_type(const char *filename)
{
    const char *extension = get_file_extension(filename);

    if (!strcmp(extension, "gif"))
    {
        return "image/gif";
    }
    else if (!strcmp(extension, "jpg"))
    {
        return "image/jpg";
    }
    else if (!strcmp(extension, "jpeg"))
    {
        return "image/jpeg";
    }
    else if (!strcmp(extension, "png"))
    {
        return "image/png";
    }
    else if (!strcmp(extension, "ico"))
    {
        return "image/ico";
    }
    else if (!strcmp(extension, "zip"))
    {
        return "image/zip";
    }
    else if (!strcmp(extension, "gz"))
    {
        return "image/gz";
    }
    else if (!strcmp(extension, "tar"))
    {
        return "image/tar";
    }
    else if (!strcmp(extension, "htm"))
    {
        return "text/html";
    }
    else if (!strcmp(extension, "html"))
    {
        return "text/html";
    }
    else if (!strcmp(extension, "txt"))
    {
        return "text/txt";
    }
    else {
        return NULL;
    }
}


/**
* @brief char *last_mod_time(struct stat fileattrib)
*
* Dada la estructura de datos relevantes de un fichero, devuelve el campo de última fecha de modificacion, formateado.
*
* @ingroup Serverlib
* @param fileattrib - Estructura que contiene datos relevantes de un fichero, sacada mediante la funcion stat(...).
* @return char* - String con el tiempo de última modificación del fichero, formateada.
*/
char *last_mod_time(struct stat fileattrib)
{
    struct tm *last_modified;
    char *last_mod_buf = malloc(sizeof(char) * MAX_STR);

    last_modified = gmtime(&(fileattrib.st_mtime));
    strftime(last_mod_buf, sizeof(char) * MAX_STR, "%a, %d %b %Y %H:%M:%S %Z", last_modified);
    return last_mod_buf;
}


/**
* @brief char *real_time()
*
* Devuelve el tiempo actual usando la funcion gmtime.
*
* @ingroup Serverlib
* @return char* - String con el tiempo actual formateada.
*/
char *real_time()
{
    time_t rawtime;
    struct tm timeinfo, *last_modified;
    char *time_buf = malloc(sizeof(char) * MAX_STR);

    time(&rawtime);
    timeinfo = *gmtime(&rawtime);
    strftime(time_buf, sizeof(char) * MAX_STR, "%a, %d %b %Y %H:%M:%S %Z", &timeinfo);
    return time_buf;
}
