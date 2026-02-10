// Daniel Coelho Pereira 2021237092
// Eduardo Luís Pereira Marques 2022231584

#ifndef UTILS_H
#define UTILS_H

#include <stdio.h>
#include <semaphore.h>
#include <time.h>

#define CONFIG_FILE "config.cfg"
#define LOG_FILE "DEIChain_log.txt"
#define SEM_NAME "log_semaphore"
#define SEM_POOL_NAME "pool_semaphore"
#define SEM_LEDGER_NAME "sem_blockchain_ledger"
#define key_pool 1234
#define key_ledger 4321
#define VALIDATOR_PIPE "VALIDATOR_INPUT"
#define MSG_QUEUE_KEY 5678
#define HASH_SIZE 65

#define TX_ID_LEN 64
#define TXB_ID_LEN 64

#define STRATEGY_RANDOM 0
#define STRATEGY_HIGHEST_REWARD 1  
#define STRATEGY_LOWEST_REWARD 2

// Global variable accessible to all files that include utils.h
extern size_t transactions_per_block;

// Estrutura para armazenar configurações do sistema
typedef struct {
    int num_miners;
    int pool_size;
    int transactions_per_block;
    int blockchain_blocks;
} Config;

// Estrutura que representa uma transação
typedef struct {
    int transaction_id;
    int reward;
    int sender_id;
    int receiver_id;
    float value;
    time_t timestamp;
    int age;
    int empty;
} Transaction;

// Estrutura que representa um bloco da blockchain
typedef struct {
    int block_id;
    int miner_id;
    char previous_block_hash[HASH_SIZE];
    time_t timestamp;
    unsigned int nonce;
    Transaction transactions[];
} Block;

// Estrutura que representa a transactionPool
typedef struct {
    int count;
    int current_block_id;
    Transaction transactions[];
} TransactionPool;

// Estrutura que representa o blockchainLedger
typedef struct {
    int count;
    Block blocks[];
} BlockchainLedger;

// Estrutura que representa o messageQueue
typedef struct {
    long mtype;
    int verify;
    int block_id;
    int miner_id;
    int transaction_count;
    float total_value;
    float total_reward;
    long time_total;
    int time_count;
} MessageQueue;

// Utility functions
void process_config(Config *config);
void log_message(char *sender, char *message, FILE *log_file, sem_t *sem);
size_t get_transaction_block_size();

#endif