#ifndef SERVIDOR_H
#define SERVIDOR_H

#include <sys/socket.h>
#include <sys/types.h>
#include <netinet/in.h>
#include <unistd.h>
#include <stdlib.h>
#include <stdio.h>
#include <netdb.h>
#include <string.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <time.h>
#include <arpa/inet.h>
#include <sys/ipc.h>
#include <sys/shm.h>

#define BUF_SIZE    1024
#define MAX_CLIENTES    200
#define MAX_STRING  100
#define LINHA_SIZE  100
#define BUF_SIZE    1024
#define BUFLEN  512

typedef struct{
    char nome[MAX_STRING];
    int socket;
    char multicast[MAX_STRING];
    int tamanho_atual;
    int tamanho_max;
} Turma;

typedef struct{
    char nome[MAX_STRING];
    char pass[MAX_STRING];
    char funcao[MAX_STRING];
    int turmas_inscrito;
    Turma turmas[20];
} Cliente;

void insere_clientes(Cliente *clientes, int *num_clientes, char *nome, char *pass, char *funcao);
int elimina_clientes(Cliente *clientes, int *num_clientes, char *nome);
int verifica_nome(Cliente *clientes, int *num_clientes, char *nome);
Cliente* verifica_cliente(Cliente *clientes, int *num_clientes, char *nome, char *pass);
int verifica_multicast(Turma *turmas, int num_turmas, char *multicast);
char *gerar_multicast( Turma *turmas, int num_turmas);
int create_multicast(char *multicast);
char* imprimir_clientes(Cliente *clientes, int *num_clientes);
char *imprimir_turmas(Turma *turmas, int num_turmas);
char *imprimir_subscribed(Turma *turmas, int turmasInscrito);
void process_doc(Cliente *clientes, int *num_clientes, char ficheiro[]);
void escreve_doc(Cliente *clientes, int *num_clientes, char ficheiro[]);
void erro(char *msg);

#endif 