#include "testeprojeto.h"

void insere_clientes(Cliente *clientes, int *num_clientes, char *nome, char *pass, char *funcao){
    Cliente *cliente = (Cliente *) malloc (sizeof(Cliente));
    strcpy(cliente->nome, nome);
    strcpy(cliente->pass, pass);
    strcpy(cliente->funcao, funcao);
    cliente->turmas_inscrito = 0;
    clientes[*num_clientes] = *cliente;
    (*num_clientes)++;
}

int elimina_clientes(Cliente *clientes, int *num_clientes, char *nome){
    for (int i = 0; i < *num_clientes; i++) {
        if (strcmp(clientes[i].nome, nome) == 0) {
            for (int j = i; j < *num_clientes - 1; j++) {
                clientes[j] = clientes[j + 1];
            }
            (*num_clientes)--;
            return 1;
        }
    }
    return -1;
}

int verifica_nome(Cliente *clientes, int *num_clientes, char *nome){
    for (int i = 0; i < *num_clientes; i++) {
        if (strcmp(clientes[i].nome, nome) == 0) {
            return 1;
        }
    }
    return 0;
}

Cliente* verifica_cliente(Cliente *clientes, int *num_clientes, char *nome, char *pass){
    for (int i = 0; i < *num_clientes; i++) {
        if (strcmp(clientes[i].nome, nome) == 0 && strcmp(clientes[i].pass, pass) == 0) {
            return &(clientes[i]);
        }
    }
    return NULL;
}

int verifica_multicast(Turma *turmas, int num_turmas, char *multicast){
    for(int i = 0; i < num_turmas; i++){
        if(strcmp(turmas[i].multicast, multicast) == 0){
            return 1;
        }    
    }
    return 0;
}

char *gerar_multicast(Turma *turmas, int num_turmas){
    char *str = (char*)malloc(10000 * sizeof(char));
    do{
        if(str == NULL) {
            return NULL;
        }
        str[0] = '\0';
        int aux1 = (rand() % (239 - 224 + 1)) + 224;
        int aux2 = rand() % 256;
        int aux3 = rand() % 256;
        int aux4 = rand() % 256;
        sprintf(str, "%d.%d.%d.%d", aux1, aux2, aux3, aux4);    
    } while(verifica_multicast(turmas,num_turmas, str));  
    return str;  
}

int create_multicast(char *multicast){
    struct sockaddr_in addr;
    int sock;
    if ((sock = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
        perror("socket");
        exit(1);
    }
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = inet_addr(multicast);
    addr.sin_port = htons(5000);
    int enable = 3;
    if (setsockopt(sock, IPPROTO_IP, IP_MULTICAST_TTL, &enable, sizeof(enable)) < 0){
        perror("setsockopt");
        exit(1);
    }
    return sock;
}

char* imprimir_clientes(Cliente *utilizadores, int *num_clientes) {
    char *resposta = (char*)malloc(100000 * sizeof(char));
    if (resposta == NULL) {
        return NULL;
    }
    resposta[0] = '\0';
    strcat(resposta, "\n");
    if (num_clientes == 0) {
        strcat(resposta, "\nNão existem clientes!\n");
        return resposta;
    }
    for (int i = 0; i < *num_clientes; i++) {
        char nome[100] = "";
        strcat(nome, "Nome: ");
        strcat(nome, utilizadores[i].nome);
        strcat(nome, "\nFunção: ");
        strcat(nome, utilizadores[i].funcao);
        strcat(nome, "\n");
        if (i < *num_clientes - 1) {
            strcat(nome, "\n-----------------------\n\n");
        }
        strcat(resposta, nome);
    }
    strcat(resposta, "\n");
    return resposta;
}

char *imprimir_turmas(Turma *turmas, int num_turmas){
    char *resposta = (char*)malloc(10000 * sizeof(char));
    if(num_turmas == 0){
        strcpy(resposta, "\nNão existem turmas disponíveis!\n");
        return resposta;
    }
    resposta[0] = '\0';
    strcat(resposta, "\n");
    strcat(resposta, "CLASS ");
    for(int i = 0; i < num_turmas; i++){
        char nome[100] = "";
        strcat(nome, "{");
        strcat(nome, turmas[i].nome);
        strcat(nome, "}");
        if(i != num_turmas - 1) {
            strcat(nome, ", ");
        }
        strcat(resposta, nome);
    }
    strcat(resposta, "\n");
    return resposta;
}

char *imprimir_subscribed(Turma *turmas, int num_turmas){
    char *resposta = (char*)malloc(10000 * sizeof(char));
    if (num_turmas == 0){
        strcpy(resposta, "\nO cliente não está inscrito em nenhuma turma\n");
        return resposta;
    }
    resposta[0] = '\0';
    strcat(resposta, "\n");
    strcat(resposta, "CLASS ");
    for (int i = 0; i < num_turmas; i++){
        char nome[100] = "";
        strcat(nome,"{");
        strcat(nome, turmas[i].nome);
        strcat(nome, "/");
        strcat(nome, turmas[i].multicast);
        strcat(nome,"}");
        if(i != num_turmas - 1) {
            strcat(nome, ", ");
        }
        strcat(resposta, nome);
    }
    strcat(resposta, "\n");
    return resposta;
}

void process_doc(Cliente *clientes, int *num_clientes, char ficheiro[]) {
    FILE *f = fopen(ficheiro, "r"); // abre o ficheiro
    if (f == NULL) {
        fclose(f);
        return;
    }
    char linha[LINHA_SIZE];
    while (fgets(linha, LINHA_SIZE, f)) {
        if (linha[0] == '\n' || linha[0] == '\0'){
            continue;
        }
        char nome[100], pass[100], funcao[100];
        char *str; // string que guarda os dados
        str = strtok(linha, ";");
        strcpy(nome, str); // guarda o utilizador no array de utilizadores
        if (verifica_nome(clientes,num_clientes,nome)){
            continue;
        }
        str = strtok(NULL, ";");
        strcpy(pass, str); // guarda a password no array de palavras pass
        str = strtok(NULL, ";");
        if (str[strlen(str) - 1] == '\n') {
            str[strlen(str) - 1] = '\0';
        }
        strcpy(funcao, str); // guarda a funcao no array de funcoes
        //Turma *turmas = (Turma*)malloc(sizeof(Turma));
        insere_clientes(clientes,num_clientes, nome, pass, funcao);
    }
    fclose(f);
}

void escreve_doc(Cliente *clientes, int *num_clientes, char ficheiro[]){
    FILE *documento = fopen(ficheiro, "w");
    if(documento == NULL) {
      return;
    }
    for(int i = 0; i < *num_clientes; i++){
      fprintf(documento, "%s;%s;%s", clientes[i].nome, clientes[i].pass, clientes[i].funcao);
      if(i != *num_clientes - 1){
        fprintf(documento, "\n");
      }    
    }
    fclose(documento);
}

void erro(char *msg){
	printf("Erro: %s\n", msg);
	exit(-1);
}