#include "testeprojeto.h"

void connection_tcp(Cliente *clientes, int *num_clientes, int port, int *num_turmas, Turma *turmas);
void process_client(Cliente *clientes, int *num_clientes, int client_fd, int *num_turmas, Turma *turmas);
void process_aluno(int client_fd,Cliente *cliente, int *num_turmas, Turma *turmas);
void process_professor(int client_fd,Cliente *cliente, int *num_turmas,Turma *turmas);
void connection_udp(Cliente *clientes, int *num_clientes, char ficheiro[], int port);
void signal_handler();
void cleanup();

int client_fd, s;
pid_t tcp_pid, udp_pid;

int main(int argc, char *argv[]) {
    if (argc != 4) {
        printf("Servidor {PORTO_TURMAS} {PORTO_CONFIG} {ficheiro config}\n");
        exit(-1);
    }
    int tcp_port = atoi(argv[1]);
    int udp_port = atoi(argv[2]);

    int shmid_utilizador = shmget(IPC_PRIVATE, sizeof(Cliente) * MAX_STRING + sizeof(int), IPC_CREAT | 0666);
    if (shmid_utilizador < 0) {
        erro("Erro ao criar memória partilhada");
    }
    void *shm_utilizador = shmat(shmid_utilizador, NULL, 0);
    if (shm_utilizador == (void *) -1) {
        erro("Erro ao anexar memória partilhada");
    }
    Cliente *clientes = (Cliente *) shm_utilizador;
    int *num_clientes = (int *) (shm_utilizador + sizeof(Cliente) * MAX_STRING);
    *num_clientes = 0;

    process_doc(clientes, num_clientes, argv[3]);

    int shmid = shmget(IPC_PRIVATE, sizeof(Turma) * MAX_STRING + sizeof(int), IPC_CREAT | 0666);
    if (shmid < 0) {
        erro("Erro ao criar memória partilhada");
    }
    void *shm = shmat(shmid, NULL, 0);
    if (shm == (void *) -1){
        erro("Erro ao anexar memória partilhada");
    }
    Turma *turmas = (Turma *) shm;
    int *num_turmas = (int *) (shm + sizeof(Turma) * MAX_STRING);
    *num_turmas = 0;

    signal(SIGTERM, signal_handler);
    if ((tcp_pid = fork()) == 0){
        signal(SIGTERM, signal_handler);
        connection_tcp(clientes, num_clientes, tcp_port, num_turmas, turmas);
    }
    else if (tcp_pid == -1){
        erro("fork para tcp");
    }
    if ((udp_pid = fork()) == 0){
        signal(SIGTERM, signal_handler);
        connection_udp(clientes, num_clientes, argv[3], udp_port);
    }
    else if (udp_pid == -1){
        erro("fork para udp");
    }
    while (wait(NULL) > 0);

    atexit(cleanup);
    shmdt(shm_utilizador);
    shmctl(shmid_utilizador, IPC_RMID, NULL);
    shmdt(shm);
    shmctl(shmid, IPC_RMID, NULL);
    return 0;
}

void connection_tcp(Cliente *clientes, int *num_clientes,int port, int *num_turmas, Turma *turmas){
    int fd, client;
    struct sockaddr_in addr, client_addr;
    int client_addr_size = client_addr_size = sizeof(client_addr);

    bzero((void *) &addr, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = htonl(INADDR_ANY);
    addr.sin_port = htons(port);

    if ( (fd = socket(AF_INET, SOCK_STREAM, 0)) < 0)
        erro("na funcao socket");
    if ( bind(fd,(struct sockaddr*)&addr,sizeof(addr)) < 0)
        erro("na funcao bind");
    if( listen(fd, 5) < 0)
        erro("na funcao listen");

    while (1) {
        while(waitpid(-1,NULL,WNOHANG)>0);
        client = accept(fd,(struct sockaddr *)&client_addr,(socklen_t *)&client_addr_size);
        if (client > 0) {
            if (fork() == 0) {
                close(fd);
                process_client(clientes,num_clientes,client,num_turmas,turmas);
                exit(0);
            }
        }
        close(client);
    }
}

void process_client(Cliente *clientes, int *num_clientes, int client_fd,int *num_turmas, Turma *turmas){
    int nread = 0;
    char buffer[BUF_SIZE];
    char *iniciar = "Introduza os dados da sua conta para inciar a sessão:"; // string que guarda a mensagem inicial
    char *terminar = "Até logo!"; // string que guarda a mensagem final
    write(client_fd,iniciar, strlen(iniciar)); // envia a mensagem inicial ao cliente
    do {
        nread = read(client_fd, buffer, BUF_SIZE-1);
        buffer[nread] = '\0';
        fflush(stdout);
        if(strcmp(buffer,"SAIR") == 0){ // se o cliente escrever "SAIR"
            write(client_fd,terminar,strlen(terminar)); // envia a mensagem final ao cliente
            break;
        }
        char *aux[100]; // array que guarda as palavras do buffer
        char *str;
        str = strtok(buffer," "); // divisao do buffer
        int j;
        for(j = 0; str != NULL; j++){
            aux[j] = str;
            str = strtok(NULL," ");
        }
        for(int i = j; i < 100; i++){
            aux[i] = " ";
        }
        char *resposta = (char*)malloc(1000 * sizeof(char)); // string que guarda a resposta do server
        int verifica = 1; // flag para verificar se o login foi efetuado
        Cliente *cliente = NULL;
        if(strcmp(aux[0],"LOGIN") == 0){ // verifica se o client escreveu LOGIN
            cliente = verifica_cliente(clientes,num_clientes,aux[1],aux[2]);
            if(cliente != NULL && (strcmp(cliente->funcao, "aluno") == 0 || strcmp(cliente->funcao, "professor") == 0)){
                resposta = "OK\n"; // a resposta fica OK
                verifica = 0; // altera o valor da flag
            } 
            if(verifica){ // se nao encontrar a conta
                resposta = "REJECTED\n"; // a resposta fica REJECTED
            }
        }
        else{ // se o cliente nao escrever LOGIN
            resposta = "\nUSE: LOGIN <utilizador> <password>\n"; // a resposta fica esta dica
        }
        write(client_fd, resposta, strlen(resposta)); // // envia a resposta ao cliente
        if(verifica == 0){ // se o login foi efetuado com sucesso
            if(strcmp(cliente->funcao,"aluno") == 0){ // verifica se a funcao do cliente é aluno
                process_aluno(client_fd,cliente,num_turmas,turmas); // chamada da funcao que processa os alunos
                close(client_fd);
                break;
            }
            else if(strcmp(cliente->funcao,"professor") == 0){ // verifica se a funcao do cliente é professor
                process_professor(client_fd,cliente,num_turmas,turmas); // chamada da funcao que processa os professores
                close(client_fd);
                break;
            }
        }
    } while (nread>0);
    close(client_fd);
}

void process_aluno(int client_fd, Cliente *cliente, int *num_turmas, Turma *turmas){
	int nread = 0;
    char buffer[BUF_SIZE];
    char *terminar = "Sessão terminada!"; // string que guarda a mensagem do termino da sessao
    do {
        nread = read(client_fd, buffer, BUF_SIZE-1);
        buffer[nread] = '\0';
        fflush(stdout);
        if(strcmp(buffer,"SAIR") == 0){ // se o cliente escrever TERMINAR a sessao é terminada
            write(client_fd,terminar,strlen(terminar)); // envia a mensagem ao cliente
            break;
        }
        int contador = 0;
        char *aux[100]; // array que guarda as palavras do buffer
        char *str;
        str = strtok(buffer," ");
        for(int i = 0; str != NULL; i++){ // divisao do buffer
            aux[i] = str;
            str = strtok(NULL," ");
            contador++;
        }
        // conjunto de mensagens disponiveis ao aluno
        char *resposta = (char*)malloc(1000 * sizeof(char));
        if(strcmp(aux[0],"LIST_CLASSES") == 0){
            resposta = imprimir_turmas(turmas, *num_turmas);
        }  
        else if(strcmp(aux[0],"LIST_SUBSCRIBED") == 0){
            resposta = imprimir_subscribed(cliente->turmas,cliente->turmas_inscrito);
        } 
        else if(strcmp(aux[0],"SUBSCRIBE_CLASS") == 0){
            int i;
            int encontrado = 0;
            if (contador == 2){
                for (i = 0; i < *num_turmas; i++){
                    if(strcmp(turmas[i].nome,aux[1]) == 0){
                        encontrado = 1;
                        if (turmas[i].tamanho_max > turmas[i].tamanho_atual){
                            int verifica = 0;
                            for (int j = 0; j < cliente->turmas_inscrito; j++){
                                if (strcmp(cliente->turmas[j].nome,aux[1]) == 0){
                                    verifica = 1;
                                    break;
                                }
                            }
                            if (verifica == 0){
                                struct sockaddr_in addr;
                                int sock;
                                if ((sock = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
                                    perror("socket");
                                    close(sock);
                                    exit(1);
                                }
                                int reuse = 1;
                                if (setsockopt(sock, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof(reuse)) < 0) {
                                    perror("SO_REUSEADDR");
                                    close(sock);
                                    exit(1);
                                }
                                memset(&addr, 0, sizeof(addr));
                                addr.sin_family = AF_INET;
                                addr.sin_addr.s_addr = inet_addr(turmas[i].multicast);
                                addr.sin_port = htons(5000);
                                if (bind(sock, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
                                    perror("bind");
                                    close(sock);
                                    exit(1);
                                }
                                struct ip_mreq mreq;
                                mreq.imr_multiaddr.s_addr = inet_addr(turmas[i].multicast);
                                mreq.imr_interface.s_addr = INADDR_ANY;
                                if(setsockopt(turmas[i].socket, IPPROTO_IP, IP_ADD_MEMBERSHIP, &mreq, sizeof(mreq)) < 0) {
                                    erro("setsockopt");
                                    close(sock);
                                    exit(1);
                                }
                                turmas[i].tamanho_atual++;
                                cliente->turmas[cliente->turmas_inscrito] = turmas[i];
                                cliente->turmas_inscrito++;
                                sprintf(resposta,"\nACCEPTED %s\n",turmas[i].multicast);
                                break;
                            }
                            else{
                                sprintf(resposta, "%s", "\nO professor já está inscrito nessa turma!\n");
                            }
                        }
                        else{
                            strcpy(resposta, "\nREJECTED\n");
                            break;
                        }
                    }
                }
                if (encontrado == 0){
                    strcpy(resposta, "\nNão existe nenhuma turma com esse nome!\n");
                }    
            }
        } 
        else{
            resposta = "\nCHOSE FROM: LIST_CLASSES or LIST_SUBSCRIBED or SUBSCRIBED_CLASS <name>\n";
        }
        write(client_fd, resposta, strlen(resposta)); // envia a resposta ao cliente
    } while (nread>0);
}

void process_professor(int client_fd, Cliente *cliente, int *num_turmas, Turma *turmas){
	int nread = 0;
    char buffer[BUF_SIZE];
    char *terminar = "Sessão terminada!"; // string que guarda a mensagem do termino da sessao
    do {
        nread = read(client_fd, buffer, BUF_SIZE-1);
        buffer[nread] = '\0';
        fflush(stdout);
        if(strcmp(buffer,"SAIR") == 0){ // se o cliente escrever TERMINAR a sessao é terminada
            write(client_fd,terminar,strlen(terminar)); // envia a mensagem ao cliente
            break;
        }
        int contador = 0;
        char *aux[100]; // array que guarda as palavras do buffer
        char *str;
        str = strtok(buffer," ");
        for(int i = 0; str != NULL; i++){ // divisao do buffer
            aux[i] = str;
            str = strtok(NULL," ");
            contador++;
        }
        // conjunto de mensagens disponiveis ao professor
        char *resposta = (char*)malloc(1000 * sizeof(char));
        if(strcmp(aux[0],"LIST_CLASSES") == 0){
            resposta = imprimir_turmas(turmas,*num_turmas);
        }  
        else if(strcmp(aux[0],"LIST_SUBSCRIBED") == 0){
            resposta = imprimir_subscribed(cliente->turmas,cliente->turmas_inscrito);
        } 
        else if(strcmp(aux[0],"SUBSCRIBE_CLASS") == 0){
            int i;
            int encontrado = 0;
            if (contador == 2){
                for (i = 0; i < *num_turmas; i++){
                    if(strcmp(turmas[i].nome,aux[1]) == 0){
                        encontrado = 1;
                        if (turmas[i].tamanho_max > turmas[i].tamanho_atual){
                            int verifica = 0;
                            for (int j = 0; j < cliente->turmas_inscrito; j++){
                                if (strcmp(cliente->turmas[j].nome,aux[1]) == 0){
                                    verifica = 1;
                                    break;
                                }
                            }
                            if (verifica == 0){
                                struct sockaddr_in addr;
                                int sock;
                                if ((sock = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
                                    perror("socket");
                                    close(sock);
                                    exit(1);
                                }
                                int reuse = 1;
                                if (setsockopt(sock, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof(reuse)) < 0) {
                                    perror("SO_REUSEADDR");
                                    close(sock);
                                    exit(1);
                                }
                                memset(&addr, 0, sizeof(addr));
                                addr.sin_family = AF_INET;
                                addr.sin_addr.s_addr = inet_addr(turmas[i].multicast);
                                addr.sin_port = htons(5000);
                                if (bind(sock, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
                                    perror("bind");
                                    close(sock);
                                    exit(1);
                                }
                                struct ip_mreq mreq;
                                mreq.imr_multiaddr.s_addr = inet_addr(turmas[i].multicast);
                                mreq.imr_interface.s_addr = INADDR_ANY;
                                if(setsockopt(turmas[i].socket, IPPROTO_IP, IP_ADD_MEMBERSHIP, &mreq, sizeof(mreq)) < 0) {
                                    erro("setsockopt");
                                    close(sock);
                                    exit(1);
                                }
                                turmas[i].tamanho_atual++;
                                cliente->turmas[cliente->turmas_inscrito] = turmas[i];
                                cliente->turmas_inscrito++;
                                sprintf(resposta,"\nACCEPTED %s\n",turmas[i].multicast);
                                break;
                            }
                            else{
                                sprintf(resposta, "%s", "\nO professor já está inscrito nessa turma!\n");
                            }
                        }
                        else{
                            strcpy(resposta, "\nREJECTED\n");
                            break;
                        }
                    }
                }
                if (encontrado == 0){
                    strcpy(resposta, "\nNão existe nenhuma turma com esse nome!\n");
                }    
            }
        }
        else if(strcmp(aux[0],"CREATE_CLASS") == 0){
            if(contador >= 3){
                int verifica = 0;
                for(int i = 0; i < *num_turmas; i++){
                    if (strcmp(turmas[i].nome, aux[1]) == 0){
                        verifica = 1;
                        break;
                    }
                }
                if (verifica == 0){
                    Turma *aux_turma = (Turma*)malloc(sizeof(Turma));
                    if(aux_turma != NULL){
                        char *aux_multicast = gerar_multicast(turmas, *num_turmas);
                        sprintf(resposta, "\nOK %s\n", aux_multicast);
                        int socket = create_multicast(aux_multicast);
                        strcpy(aux_turma->nome,aux[1]);
                        aux_turma->socket = socket;
                        strcpy(aux_turma->multicast,aux_multicast);
                        aux_turma->tamanho_max = atoi(aux[2]);
                        aux_turma->tamanho_atual = 0;
                        turmas[*num_turmas] = *aux_turma;
                        (*num_turmas)++;
                    }
                }
                else{
                    resposta = "\nJá existe uma turma com esse nome!\n"; 
                }
            }
            else {
                resposta = "\nUSE: CREATE_CLASS <nome> <tamanho>\n"; 
            }
        }  
        else if(strcmp(aux[0],"SEND") == 0){
            int i;
            int encontrado = 0;
            if (contador == 3){
                for (i = 0; i < *num_turmas; i++){
                    if(strcmp(turmas[i].nome,aux[1]) == 0){
                        encontrado = 1;
                        struct sockaddr_in addr;
                        memset(&addr, 0, sizeof(addr));
                        addr.sin_family = AF_INET;
                        int verifica = 0;
                        for(int j = 0; j < cliente->turmas_inscrito ; j++){
                            if (strcmp(cliente->turmas[j].nome, turmas[i].nome) == 0){
                                verifica = 1;
                                break;
                            }
                        }
                        if (verifica == 1){
                            strcpy(resposta,"\nMensagem enviada com sucesso!\n");
                            addr.sin_addr.s_addr = inet_addr(turmas[i].multicast);
                            addr.sin_port = htons(5000);
                            if (sendto(turmas[i].socket, aux[2], strlen(aux[2]), 0, (struct sockaddr *)&addr, sizeof(addr)) < 0){
                                erro("sendto");
                                exit(1);
                            } 
                        }
                        else{
                            sprintf(resposta, "\n%s\n","O professor não está inscrito nessa turma!");
                        }
                    }
                }
                if (encontrado == 0){
                    strcpy(resposta, "\nNão existe turma com esse nome!\n");
                }    
            }
            else {
                resposta = "\nUSE: SEND <nome> <mensagem>\n"; 
            }
        } 
        else{
            resposta = "\nCHOSE FROM: LIST_CLASSES or LIST_SUBSCRIBED or SUBSCRIBE_CLASS <name> or CREATE_CLASS {name} {size} or SEND {name} {text}\n";
        }
        write(client_fd, resposta, strlen(resposta)); // envia a resposta ao cliente
    } while (nread>0);
}

void connection_udp(Cliente *clientes, int *num_clientes, char ficheiro[], int port){
    struct sockaddr_in si_minha, si_outra;
	int s;
    int recv_len;
    socklen_t slen = sizeof(si_outra);
    char buf[BUFLEN];

	// Cria um socket para recepção de pacotes UDP
	if((s=socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)) == -1) {
		erro("Erro na criação do socket");
	}
  	// Preenchimento da socket address structure
	si_minha.sin_family = AF_INET;
	si_minha.sin_port = htons(port);
	si_minha.sin_addr.s_addr = htonl(INADDR_ANY);

	// Associa o socket à informação de endereço
	if(bind(s,(struct sockaddr*)&si_minha, sizeof(si_minha)) == -1) {
		erro("Erro no bind");
	}
    int verifica = 0;
    while(1){
        if((recv_len = recvfrom(s, buf, BUFLEN, 0, (struct sockaddr *) &si_outra, (socklen_t *)&slen)) == -1) {
            erro("Erro no recvfrom");
        }
        buf[recv_len - 1] = '\0';
        int contador = 0;
        char *aux[100]; // array que guarda as palavras do buffer
        char *str;
        str = strtok(buf," ");
        int j;
        for(j = 0; str != NULL; j++){ // divisao do buffer
            aux[j] = str;
            str = strtok(NULL," ");
            contador++;
        }
        for(int i = j; i < 100; i++){
            aux[i] = " ";
        }
        char *resposta = (char*)malloc(1000 * sizeof(char));
        Cliente *cliente = NULL;
        if(verifica == 0){ 
            if(strcmp(aux[0],"LOGIN") == 0){
                cliente = verifica_cliente(clientes,num_clientes,aux[1],aux[2]);
                if(cliente != NULL && strcmp(cliente->funcao, "administrador") == 0){
                    resposta = "OK\n\n"; // a resposta fica OK
                    verifica = 1; // altera o valor da flag
                        
                }
                else { // se nao encontrar a conta
                    resposta = "REJECTED (THIS USER ISN'T AN ADMIN)\n\n"; // a resposta fica REJECTED
                } 
            }    
            else{ // se o cliente nao escrever LOGIN
                resposta = "\nUSE: LOGIN <utilizador> <password>\n\n"; // a resposta fica esta dica
            }
            if (sendto(s, resposta, strlen(resposta), 0, (struct sockaddr *)&si_outra, slen) == -1){ // envia a resposta ao cliente
                erro("Erro no envio da resposta");
            }
        }
        else{ // se o login foi efetuado com sucesso
            char *resposta = (char*)malloc(1000 * sizeof(char)); 
            if(strcmp(aux[0],"ADD_USER") == 0){
                if(contador == 4){
                    if (verifica_nome(clientes,num_clientes,aux[1]) == 0){
                        if((strcmp(aux[3], "aluno") == 0 || strcmp(aux[3], "professor") == 0) || strcmp(aux[3], "administrador") == 0){
                            //Turma *turmas = (Turma*)malloc(sizeof(Turma));
                            insere_clientes(clientes,num_clientes,aux[1],aux[2],aux[3]);
                            resposta = "\nCliente adicionado com sucesso!\n\n";
                        }
                        else{
                            resposta = "\nO Cliente tem de ser aluno, professor ou administrador!\n\n";
                        }
                    }
                    else{
                        resposta = "\nEsse nome já existe!\n\n";
                    }
                } 
                else {
                    resposta = "\nUSE: ADD_USER <user> <password> <administrador/aluno/professor>\n\n";
                } 
            }  
            else if(strcmp(aux[0],"DEL") == 0){
                if(contador == 2){
                    if(verifica_nome(clientes,num_clientes,aux[1])){
                        elimina_clientes(clientes,num_clientes,aux[1]);
                        resposta = "\nCliente eliminado com sucesso!\n\n";
                    }
                    else{
                        resposta = "\nNão existe nhenhum cliente com esse nome!\n\n";
                    } 
                } 
                else {
                    resposta = "\nUSE: DEL <user>\n\n";
                }
            } 
            else if(strcmp(aux[0],"LIST") == 0){
                resposta = imprimir_clientes(clientes,num_clientes);
            } 
            else if(strcmp(aux[0],"QUIT_SERVER") == 0){
                resposta = "\nServidor encerrado com successo\n";
                if (sendto(s, resposta, strlen(resposta), 0, (struct sockaddr *)&si_outra, slen) == -1){ // envia a resposta ao cliente
                    erro("Erro no envio da resposta");
                }
                escreve_doc(clientes,num_clientes,ficheiro);
                kill(tcp_pid, SIGTERM);
                kill(udp_pid, SIGTERM);
                exit(0);
            } 
            else{
                resposta = "\nCHOSE FROM: ADD_USER {username} {password} {type} or DEL {username} or LIST or QUIT_SERVER\n\n";
            }
            if (sendto(s, resposta, strlen(resposta), 0, (struct sockaddr *)&si_outra, slen) == -1){ // envia a resposta ao cliente
                erro("Erro no envio da resposta");
            } 
        } 
    }   
    close(s); 
}

void signal_handler(){
  if(tcp_pid > 0){
    kill(tcp_pid, SIGTERM);
  }
  if(udp_pid > 0){
    kill(udp_pid, SIGTERM);
  }
  cleanup();
  exit(0);
}

void cleanup(){
  if(client_fd > 0){
    close(client_fd);
  }
  if(s > 0){
    close(s);
  }
}