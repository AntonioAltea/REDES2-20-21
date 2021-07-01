#ifndef LIB_H
/**
 * @file daemon.h
 * @defgroup Serverlib Funcionalidad del servidor
 * 
 * Funcionalidad del servidor
 */

#define LIB_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <syslog.h>
#include <errno.h>
#include <pthread.h>
#include <assert.h>
#include <unistd.h>
#include <sys/types.h>
#include <signal.h>
#include <time.h>
#include <sys/stat.h>

#define MAX_STR 2048
#define WORD_SIZE 2048
#define CONFIG_NAME "server.conf"
#define IP "192.168.1.149"

/**
* @brief ConfigArgs* read_config_file();
* 
* Lee el fichero de configuracion del servidor y crea y rellena
* los campos de una estructura donde guarda esa configuracion.
*
* @ingroup Serverlib
* @return ConfigArgs* - Puntero a la estructura ConfigArgs creada y rellenada.
*/
struct ConfigArgs* read_config_file();


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
int start_server(struct ConfigArgs* args);


/**
* @brief void* task(void* args)
*
* Parsea una peticion HTTP, guardando su informacion, y llama al metodo GET, POST o OPTIONS. Es ejecutada por un thread.
*
* @ingroup Serverlib
* @param args Puntero a una estructura que contiene la configuracion del servidor.
* @return NULL en cualquier caso, si ha habido un error se plasma en forma de respuesta HTTP y no como un return.
*/
void* task(void* args);


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
void manage_get(char *time_buf, char *path_str, struct ConfigArgs *configarguments);


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
void manage_post(char *time_buf, char *path_str, struct ConfigArgs *configarguments, char *body);


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
void manage_options(char *time_buf, struct ConfigArgs *arguments);


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
void serve_file(char *fichero, char *time_buf, struct ConfigArgs *arguments);


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
int exe_script(char* time_buf, char* fichero, char* arguments, struct ConfigArgs *configarguments);


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
void file_doesnt_exist(char *time_buf, struct ConfigArgs *arguments);


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
void not_supported_verb(char* time_buf, struct ConfigArgs *arguments);


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
const char *get_content_type(const char *filename);


/**
* @brief const char *get_file_extension(const char *filename)
*
* Devuelve la extension de un fichero (a partir del punto). Para ello recibe una string de entrada.
*
* @ingroup Serverlib
* @param filename Nombre de un fichero a analizar.
* @return String que contiene la extension a partir del punto en caso de que la string inicial tuviera extension, una string vacia en caso contrario.
*/
const char *get_file_extension(const char *filename);


/**
* @brief char *last_mod_time(struct stat fileattrib)
*
* Dada la estructura de datos relevantes de un fichero, devuelve el campo de última fecha de modificacion, formateado.
*
* @ingroup Serverlib
* @param fileattrib - Estructura que contiene datos relevantes de un fichero, sacada mediante la funcion stat(...).
* @return char* - String con el tiempo de última modificación del fichero, formateada.
*/
char *last_mod_time(struct stat fileattrib);


/**
* @brief char *real_time()
* 
* Devuelve el tiempo actual usando la funcion gmtime.
*
* @ingroup Serverlib
* @return char* - String con el tiempo actual formateada.
*/
char *real_time();

/**
 * @brief ConfigArgs
 * 
 * @ingroup Serverlib
 * Estructura que almacena variables de configuración
 */
struct ConfigArgs {
    int socketDesc; /**< socketDesc */
    int port; /**< Puerto en el que escucha el servidor*/
    int max_clients; /**< Número máximo de clientes para el servidor*/
    char server_root[WORD_SIZE]; /**< server_root*/
    char server_signature[WORD_SIZE]; /**< server_signature*/
};

#endif
