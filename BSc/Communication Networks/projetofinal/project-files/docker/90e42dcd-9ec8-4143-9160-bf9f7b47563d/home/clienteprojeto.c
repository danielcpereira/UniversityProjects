#include <stdio.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <netdb.h>

#define BUF_SIZE 1024

void erro(char *msg);
void mensagens(int server_fd);

int main(int argc, char *argv[]) {
  char endServer[100];
  char buffer[BUF_SIZE];
  int fd;
  struct sockaddr_in addr;
  struct hostent *hostPtr;

  if (argc != 3) {
    printf("cliente <host> <port>\n");
    exit(-1);
  }

  strcpy(endServer, argv[1]);
  if ((hostPtr = gethostbyname(endServer)) == 0)
    erro("Não consegui obter endereço");

  bzero((void *) &addr, sizeof(addr));
  addr.sin_family = AF_INET;
  addr.sin_addr.s_addr = ((struct in_addr *)(hostPtr->h_addr))->s_addr;
  addr.sin_port = htons((short) atoi(argv[2]));

  if ((fd = socket(AF_INET,SOCK_STREAM,0)) == -1)
	  erro("socket");
  if (connect(fd,(struct sockaddr *)&addr,sizeof (addr)) < 0)
	  erro("Connect");
  mensagens(fd); // mensagem inical enviada pelo server
  while(1){
    do{
      fgets(buffer,BUF_SIZE,stdin); // guarda na string buffer a mensagem do cliente
    } while(strcmp(buffer,"\n") == 0);
    buffer[strlen(buffer) - 1] = '\0'; // remover o "\n" da mensagem
    write(fd,buffer,strlen(buffer) + 1); // envia essa mensagem para o server
    mensagens(fd); // recebe a respetiva resposta enviada pelo server
    if(strcmp(buffer,"SAIR") == 0){ // se o cliente escrever "SAIR" termina o programa
      break;
    }
  }
  close(fd);
  exit(0);
}

void mensagens(int server_fd){ // funcao que le as mensagens do server
  char buffer[BUF_SIZE];
  int nread = 0;
  nread = read(server_fd, buffer, BUF_SIZE - 1);
  if (nread > 0){
    buffer[nread] = '\0';
    printf("%s\n",buffer);
  }
}

void erro(char *msg) {
  printf("Erro: %s\n", msg);
	exit(-1);
}