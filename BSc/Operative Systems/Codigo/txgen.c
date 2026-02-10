// Daniel Coelho Pereira 2021237092
// Eduardo Luís Pereira Marques 2022231584

#include "controller.h"
#include "utils.h"
#include <stdio.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ipc.h>
#include <sys/shm.h>
#include <semaphore.h>
#include <fcntl.h>
#include <time.h>

extern pthread_mutex_t mining_mutex;
extern pthread_cond_t mining_cond;
extern int terminar;

// Função principal que inicializa o gerador de transações
int main(int argc, char *argv[]){
    int reward;
    int sleep_time;
    if (argc != 3) {
        fprintf(stderr,"MUST USE: ./txgen <reward> <sleep_time>!\n");
        exit(1);
    }
    reward = atoi(argv[1]);
    if (reward < 1 || reward > 3){
        fprintf(stderr,"<reward> MUST BE 1 TO 3!\n");
        exit(1);
    }
    sleep_time = atoi(argv[2]);
    if (sleep_time < 200 || sleep_time > 3000){
        fprintf(stderr,"<sleep_time> MUST BE 200 TO 3000!\n");
        exit(1);
    }
    FILE *log_file = fopen(LOG_FILE, "a+");
    if (log_file == NULL) {
        perror("ERROR OPENING LOG FILE");
        exit(EXIT_FAILURE);
    }
    sem_t *sem = sem_open(SEM_NAME, O_CREAT, 0644, 1);
    if (sem == SEM_FAILED) {
        perror("ERROR OPENING SEM");
        exit(EXIT_FAILURE);
    }
    char message[100];
    printf("TRANSACTION GENERATOR CREATED WITH REWARD: %d AND SLEEP_TIME: %d!\n", reward, sleep_time);
    snprintf(message, sizeof(message), "TRANSACTION GENERATOR CREATED WITH REWARD: %d AND SLEEP_TIME: %d!", reward, sleep_time);
    log_message("TXGEN", message, log_file, sem);

    Config config;
    process_config(&config);
    size_t pool_size = sizeof(TransactionPool) + config.pool_size * sizeof(Transaction);

    int shmid_pool = shmget(key_pool, pool_size, 0777);
    if (shmid_pool == -1) {
        perror("ERROR ACCESSING TRANSACTION POOL SHARED MEMORY");
        exit(EXIT_FAILURE);
    }
    
    TransactionPool *transaction_pool = (TransactionPool *)shmat(shmid_pool, NULL, 0);
    if (transaction_pool == (void *)-1) {
        perror("ERROR ATTACHING TO TRANSACTION POOL SHARED MEMORY");
        exit(EXIT_FAILURE);
    }
    
    sem_t *sem_pool = sem_open(SEM_POOL_NAME, O_CREAT, 0644, 1);
    if (sem_pool == SEM_FAILED) {
        perror("ERROR OPENING POOL SEM");
        shmdt(transaction_pool);
        exit(EXIT_FAILURE);
    }
    
    srand(time(NULL));

    while (1) {
        Transaction new_tx;
        new_tx.transaction_id = rand() % 100000;
        new_tx.reward = reward;
        new_tx.sender_id = rand() % 1000;
        new_tx.receiver_id = rand() % 1000;
        while (new_tx.receiver_id == new_tx.sender_id) {
            new_tx.receiver_id = rand() % 1000;
        }
        new_tx.value = ((float)(rand() % 10000)) / 100;
        new_tx.timestamp = time(NULL);
        new_tx.age = 0;
        new_tx.empty = 0;

        sem_wait(sem_pool);
        if (transaction_pool->count < config.pool_size){
            transaction_pool->transactions[transaction_pool->count] = new_tx;
            transaction_pool->count++;
            transaction_pool->transactions[transaction_pool->count].empty = 0;
            snprintf(message, sizeof(message), "NEW TRANSACTION ADDED: ID = %d, VALUE = %.2f", new_tx.transaction_id, new_tx.value);
            printf("%s\n", message);
            log_message("TXGEN", message, log_file, sem);
        }
        else {
            log_message("CONTROLLER", "TRANSACTION POOL IS FULL. TRANSACTION DISCARDED", log_file, sem);
            printf("TRANSACTION POOL IS FULL. TRANSACTION DISCARDED\n");
        }
        //printf("%d\n", transaction_pool->count);
        sem_post(sem_pool);

        usleep(sleep_time * 1000);
    }

    shmdt(transaction_pool);

    return 0;
}
