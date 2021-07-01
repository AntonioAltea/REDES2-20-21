#include <unistd.h> /* for fork */
#include <sys/types.h> /* for pid_t */
#include <sys/wait.h> /* for wait */
#include <stdio.h>
#include <stdlib.h>


int main(int argc,char** argv)
{
    if (argc < 2){
        printf("Indica el número de procesos\n");
        exit(EXIT_FAILURE);
    }

    for(int i = 0; i < atoi(argv[1]); i++){
        pid_t pid=fork();
        if (pid < 0)
        {
            exit(EXIT_FAILURE);
        }
        if (pid == 0)
        {
            execv("client", (char**){NULL});
            exit(EXIT_SUCCESS);
        }
    }
    for(int i = 0; i < atoi(argv[1]); i++) wait(NULL);
    exit(EXIT_SUCCESS);
}