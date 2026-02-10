// Daniel Coelho Pereira 2021237092
// Eduardo Luís Pereira Marques 2022231584

#include "utils.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <semaphore.h>

// Global variable accessible to all files that include utils.h
size_t transactions_per_block;

// Função que lê e processa as configurações a partir do ficheiro
void process_config(Config *config) {
    FILE *file = fopen(CONFIG_FILE, "r");
    if (file == NULL) {
        fprintf(stderr,"Error opening config.cfg!\n");
        exit(EXIT_FAILURE);
    }
    fscanf(file, "%d\n", &config->num_miners);
    fscanf(file, "%d\n", &config->pool_size);
    fscanf(file, "%d\n", &config->transactions_per_block);
    transactions_per_block = config->transactions_per_block;
    fscanf(file, "%d\n", &config->blockchain_blocks);
    fclose(file);
}

// Função que grava as mensagens no ficheiro log utilizando um semáforo
void log_message(char *sender, char *message, FILE *log_file, sem_t *sem) {
    sem_wait(sem);
    time_t aux;
    struct tm* tm_info;
    aux = time(NULL);
    tm_info = localtime(&aux);
    fprintf(log_file, "[%02d:%02d:%02d] %s: %s\n", tm_info->tm_hour, tm_info->tm_min, tm_info->tm_sec, sender, message);
    fflush(log_file);
    sem_post(sem);
}

// Inline function to compute the size of a TransactionBlock
size_t get_transaction_block_size() {
    if (transactions_per_block == 0) {
        perror("Must set the 'transactions_per_block' variable before using!\n");
        exit(-1);
    }
    return sizeof(Block) + transactions_per_block * sizeof(Transaction);
}