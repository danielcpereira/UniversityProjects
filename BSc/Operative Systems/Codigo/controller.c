// Daniel Coelho Pereira 2021237092
// Eduardo Luís Pereira Marques 2022231584

#include "controller.h"
#include "utils.h"
#include "pow.h"
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <signal.h>
#include <sys/shm.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <string.h>

#define key_ledger 4321
#define MESSAGE_SIZE 200
#define MAX_VALIDATORS 3

Config config;

char hash_buffer[HASH_SIZE] = INITIAL_HASH;

pid_t id_validators[MAX_VALIDATORS];
int num_validators = 0;

int shmid_pool, shmid_ledger;
pid_t miner_pid, validator_pid, statistics_pid;
pthread_t *miners = NULL;
FILE *log_file;
sem_t *sem, *sem_pool, *sem_ledger;

pthread_t thread_validators_ctrl;
int id_validators_ctrl;

int pipe_fd;
int msgq_id;

int *valid_miners = NULL;
int *invalid_miners = NULL;
int blocks_count = 0;
int *credits_miners = NULL;
int max_miners = 0;

long stats_sum_delay = 0;
long stats_count = 0;

int terminar = 0;

// Função que imprime informações de um bloco
void print_block_info(Block *block) {
    printf("Block ID: %d\n", block->block_id);
    printf("Previous Hash:\n%s\n", block->previous_block_hash);
    printf("Block Timestamp: %ld\n", block->timestamp);
    printf("Nonce: %u\n", block->nonce);
    printf("Transactions:\n");
    for (int i = 0; i < (int)transactions_per_block; ++i) {
        Transaction tx = block->transactions[i];
        printf("  [%d] ID: %d | Reward: %d | Value: %.2f | Timestamp: %ld\n", i, tx.transaction_id, tx.reward, tx.value, tx.timestamp);
    }
}

// Função que escreve um bloco na blockchain ledger
int write_block_to_ledger(Block *block) {
    char message[100];
    Config config;
    process_config(&config);
    int shmid_ledger = shmget(key_ledger, 0, 0777);
    if (shmid_ledger == -1) {
        perror("ERROR GETTING SHARED MEMORY ID FOR LEDGER");
        return 0;
    }
    BlockchainLedger *blockchain_ledger = (BlockchainLedger *)shmat(shmid_ledger, NULL, 0);
    if (blockchain_ledger == (void *)-1) {
        perror("ERROR ATTACHING TO SHARED MEMORY FOR LEDGER");
        return 0;
    }
    sem_wait(sem_ledger);
    if (blockchain_ledger->count >= config.blockchain_blocks) {
        snprintf(message, sizeof(message), "BLOCKCHAIN LEDGER IS FULL, CANNOT ADD BLOCK %d", block->block_id);
        log_message("CONTROLLER", message, log_file, sem);
        shmdt(blockchain_ledger);
        return 0;
    }
    
    size_t block_size = sizeof(Block) + transactions_per_block * sizeof(Transaction);
    char *ledger_data = (char *)blockchain_ledger;
    size_t offset = sizeof(BlockchainLedger) + blockchain_ledger->count * block_size;
    Block *target_block = (Block *)(ledger_data + offset);
    
    memcpy(target_block, block, sizeof(Block));
    
    for (unsigned int i = 0; i < transactions_per_block; i++) {
        memcpy(&(target_block->transactions[i]), &(block->transactions[i]), sizeof(Transaction));
    }

    blockchain_ledger->count++;

    sem_post(sem_ledger);
    
    snprintf(message, sizeof(message), "BLOCK %d SUCCESSFULLY ADDED TO BLOCKCHAIN AT POSITION %d", block->block_id, blockchain_ledger->count - 1);
    log_message("VALIDATOR", message, log_file, sem);
    
    shmdt(blockchain_ledger);
    
    return 1;
}

// Função que emprime a blockchain ledger
void dump_ledger() {
    int shmid_ledger = shmget(key_ledger, 0, 0777);
    if (shmid_ledger == -1) {
        perror("ERROR GETTING SHARED MEMORY ID FOR LEDGER");
        return;
    }
    BlockchainLedger *blockchain_ledger = (BlockchainLedger *)shmat(shmid_ledger, NULL, 0);
    if (blockchain_ledger == (void *)-1) {
        perror("ERROR ATTACHING TO SHARED MEMORY FOR LEDGER");
        return;
    }
    printf("\n=================== Start Ledger =================\n");
    size_t block_size = sizeof(Block) + transactions_per_block * sizeof(Transaction);
    char *ledger_data = (char *)blockchain_ledger;
    size_t header_offset = sizeof(BlockchainLedger);
    for (int i = 0; i < blockchain_ledger->count; i++) {
        size_t block_offset = header_offset + (i * block_size);
        Block *current_block = (Block *)(ledger_data + block_offset);
        printf("||----  Block %03d -- \n", i);
        printf("Block ID: %d\n", current_block->block_id);
        printf("Previous Hash:\n%s\n", current_block->previous_block_hash);
        printf("Block Timestamp: %ld\n", current_block->timestamp);
        printf("Miner ID: %d\n", current_block->miner_id);
        printf("Nonce: %u\n", current_block->nonce);
        printf("Transactions:\n");
        for (unsigned int j = 0; j < transactions_per_block; j++) {
            Transaction *tx = &(current_block->transactions[j]);
            printf("  [%d] ID: %d | Reward: %d | Value: %.2f | Timestamp: %ld\n", j, tx->transaction_id, tx->reward, tx->value, tx->timestamp);
        }
        printf("||------------------------------ \n");
    }
    printf("=================== End Ledger ===================\n");
    shmdt(blockchain_ledger);
}

void print_miner_stats() {
    int shmid_ledger = shmget(key_ledger, 0, 0777);
    if (shmid_ledger == -1) {
        perror("ERROR GETTING SHARED MEMORY ID FOR LEDGER");
        return;
    }
    BlockchainLedger *blockchain_ledger = (BlockchainLedger *)shmat(shmid_ledger, NULL, 0);
    if (blockchain_ledger == (void *)-1) {
        perror("ERROR ATTACHING TO SHARED MEMORY FOR LEDGER");
        return;
    }
    printf("\n=================== Statistics ===================\n");
    log_message("STATISTICS", "=================== Statistics ===================", log_file, sem);
    char line[128];
    for (int i = 0; i < max_miners; i++) {
        snprintf(line, sizeof(line), "Miner %d: %d valid blocks | %d invalid blocks | %d total credits", i + 1, valid_miners[i], invalid_miners[i], credits_miners[i]);
        printf("%s\n", line);
        log_message("STATISTICS", line, log_file, sem);
    }
    if (stats_count > 0) {
        double avg = (double)stats_sum_delay / stats_count;
        snprintf(line, sizeof(line),"Average transaction verification time: %.2f seconds", avg);
        printf("%s\n", line);
        log_message("STATISTICS", line, log_file, sem);
    } else {
        printf("Average transaction verification time: No transactions were processed\n");
        log_message("STATISTICS", "Average transaction verification time: No transactions were processed",log_file, sem);
    }
    snprintf(line, sizeof(line), "Block counter: %d", blocks_count);
    printf("%s\n", line);
    log_message("STATISTICS", line, log_file, sem);
    snprintf(line, sizeof(line), "Total number of blocks in the Blockchain: %d", blockchain_ledger->count);
    printf("%s\n", line);
    log_message("STATISTICS", line, log_file, sem);
    printf("=================== End Statistics ===============\n");
    log_message("STATISTICS", "=================== End Statistics ===============",log_file, sem);

    shmdt(blockchain_ledger);
}

// Função para imprimir estatisticas
void stats_sigusr1(int sig) {
    (void)sig;
    print_miner_stats();
}

// Função de handling do Sinal das estatisticas
void handle_sigusr1(int sig) {
    (void)sig;
    dump_ledger();
    kill(statistics_pid, SIGUSR1);
}

// Função executada pela thread que controla os validators
void *validators_ctrl() {
    Config config;
    process_config(&config);
    char message[100];
    TransactionPool *transaction_pool = (TransactionPool *)shmat(shmid_pool, NULL, 0);
    if (transaction_pool == (void *)-1) {
        perror("ERROR ATTACHING TO SHARED MEMORY FOR POOL");
        exit(EXIT_FAILURE);
    }
	
	 while(terminar == 0){
        	
    	sem_wait(sem_pool);

    	if((transaction_pool->count >= config.pool_size * 0.6 && num_validators == 1) || (transaction_pool->count >= config.pool_size * 0.8 && num_validators == 2)){
    		sem_post(sem_pool);
    		id_validators[num_validators] = fork();	
    		if(id_validators[num_validators] < 0){
				perror("ERROR CREATING VALIDATOR");
			}
			else if(id_validators[num_validators] == 0){
                snprintf(message, sizeof(message), "PROCESS VALIDATOR WITH PID: %ld!", (long)getpid());
                log_message("CONTROLLER", message, log_file, sem);
				validator();
    		}
    		num_validators++;
    	}	
    	else if((transaction_pool->count <= config.pool_size * 0.4) && num_validators >= 2){
    		sem_post(sem_pool);
    		for(int i = 1; i < num_validators; i++){
    			kill(id_validators[i], SIGKILL);
    		}
    	}
    	else{
    		sem_post(sem_pool);
    	}
    }
	return NULL;
}

// Função que trata do encerramento do programa
void final() {
    dump_ledger();
    //kill(statistics_pid, SIGUSR1);
    //fflush(stdout);
    printf("\nPROGRAM CLOSED!\n");
    log_message("CONTROLLER", "PROGRAM CLOSED!", log_file, sem);

    terminar = 1;

    kill(miner_pid, SIGKILL);
    for(int i = 0; i < num_validators; i++){
		kill(id_validators[i], SIGUSR2);
	}
    kill(statistics_pid, SIGKILL);

    while (wait(NULL) != -1);

    shmctl(shmid_pool, IPC_RMID, NULL);
    shmctl(shmid_ledger, IPC_RMID, NULL);

    unlink(VALIDATOR_PIPE);
    
    msgctl(msgq_id, IPC_RMID, NULL);

    fclose(log_file);
    
    sem_close(sem);

    sem_close(sem_pool);

    sem_close(sem_ledger);

    if (valid_miners != NULL) {
        free(valid_miners);
    }
    
    if (invalid_miners != NULL) {
        free(invalid_miners);
    }

    if (credits_miners != NULL) {
        free(credits_miners);
    }

    if (sem_unlink(SEM_POOL_NAME) == -1) {
        perror("ERROR REMOVING POOL SEM");
    }

    if (sem_unlink(SEM_NAME) == -1) {
        perror("ERROR REMOVING LOG SEM");
    }

    if (sem_unlink(SEM_LEDGER_NAME) == -1) {
        perror("ERROR REMOVING LEDGER SEM");
    }

    exit(0);
}

// Função principal que processa os dados do ficheiro, cria as memórias partilhadas e inicia os processos
int main(void){
    log_file = fopen(LOG_FILE, "a+");
    if (log_file == NULL) {
        perror("ERROR OPENING LOG FILE");
        exit(EXIT_FAILURE);
    }

    sem = sem_open(SEM_NAME, O_CREAT, 0644, 1);
    if (sem == SEM_FAILED) {
        perror("ERROR OPENING SEM");
        exit(EXIT_FAILURE);
    }

    sem_pool = sem_open(SEM_POOL_NAME, O_CREAT, 0644, 1);
    if (sem_pool == SEM_FAILED) {
        perror("ERROR OPENING SEM_POOL");
        exit(EXIT_FAILURE);
    }

    sem_ledger = sem_open(SEM_LEDGER_NAME, O_CREAT, 0644, 1);
    if (sem_ledger == SEM_FAILED) {
        perror("ERROR OPENING SEM_LEDGER");
        exit(EXIT_FAILURE);
    }

    Config config;
    process_config(&config);

    max_miners = config.num_miners;
    valid_miners = (int*)calloc(max_miners, sizeof(int));
    invalid_miners = (int*)calloc(max_miners, sizeof(int));
    credits_miners = (int*)calloc(max_miners, sizeof(int));
    

    for (int i = 0; i < max_miners; i++){
        valid_miners[i] = 0;
        invalid_miners[i] = 0;
        credits_miners[i] = 0;
    }
    
    printf("CONFIGURATIONS:\n");
    printf("• NUM_MINERS: %d\n", config.num_miners);
    printf("• POOL_SIZE: %d\n", config.pool_size);
    printf("• TRANSACTIONS_PER_BLOCK: %d\n", config.transactions_per_block);
    printf("• BLOCKCHAIN_BLOCKS: %d\n", config.blockchain_blocks);

    size_t pool_size = sizeof(TransactionPool) + config.pool_size * sizeof(Transaction);
    shmid_pool = shmget(key_pool, pool_size, IPC_CREAT | 0777);
    TransactionPool *transaction_pool = (TransactionPool *)shmat(shmid_pool, NULL, 0);
    transaction_pool->count = 0;
    transaction_pool->current_block_id = 0;

    for (int i = 0; i < config.pool_size; i++) {
        transaction_pool->transactions[i].empty = 1;
    }

    size_t block_size = sizeof(Block) + config.transactions_per_block * sizeof(Transaction);
    size_t ledger_size = sizeof(BlockchainLedger) + config.blockchain_blocks * block_size;
    shmid_ledger = shmget(key_ledger, ledger_size, IPC_CREAT | 0777);
    BlockchainLedger *blockchain_ledger = (BlockchainLedger *)shmat(shmid_ledger, NULL, 0);
    blockchain_ledger->count = 0;
    
    // Named Pipe
    if (mkfifo(VALIDATOR_PIPE, 0666) == -1) {
        perror("ERROR CREATING NAMED PIPE");
        exit(EXIT_FAILURE);
    }

    // Mesage Queue
    msgq_id = msgget(MSG_QUEUE_KEY, IPC_CREAT | 0666);
    if (msgq_id == -1) {
        perror("ERROR CREATING MESSAGE QUEUE");
        exit(EXIT_FAILURE);
    }

    miner_pid = fork();
    if (miner_pid == 0) {
        printf("PROCESS MINER CREATED WITH PID: %ld!\n", (long)getpid());
        char message[100];
        snprintf(message, sizeof(message), "PROCESS MINER WITH PID: %ld!", (long)getpid());
        log_message("CONTROLLER", message, log_file, sem);
        miner(config.num_miners);
        exit(0);
    }

    id_validators[num_validators] = fork();
	
	if(id_validators[num_validators] < 0){
	}
	else if(id_validators[num_validators] == 0){
		printf("PROCESS VALIDATOR CREATED WITH PID: %ld!\n", (long)getpid());
        char message[100];
        snprintf(message, sizeof(message), "PROCESS VALIDATOR WITH PID: %ld!", (long)getpid());
        log_message("CONTROLLER", message, log_file, sem);
        validator();
        exit(0);
    }
    
    num_validators++;

    statistics_pid = fork();
    if (statistics_pid == 0) {
        printf("PROCESS STATISTICS CREATED WITH PID: %ld!\n", (long)getpid());
        char message[100];
        snprintf(message, sizeof(message), "PROCESS STATISTICS WITH PID: %ld!", (long)getpid());
        log_message("CONTROLLER", message, log_file, sem);
        statistics();
        exit(0);
    }

    pthread_create(&thread_validators_ctrl, NULL, validators_ctrl, &id_validators_ctrl);

    signal(SIGINT, final);

    signal(SIGUSR1, handle_sigusr1);

    while (wait(NULL) != -1);

    return 0;
}

// Função executada por cada thread mining
void *mine(void *arg) {
    long miner_id = *((long *)arg);
    char tag[30];
    char message[100];
    int strategy;
    Config config;
    process_config(&config);

    printf("MINER THREAD %ld IS MINING...\n", miner_id);
    snprintf(message, sizeof(message), "MINING...");
    snprintf(tag, sizeof(tag), "MINER%ld", miner_id);
    log_message(tag, message, log_file, sem);

    strategy = miner_id % 3;
    
    const char *strategy_name;
    switch(strategy) {
        case STRATEGY_HIGHEST_REWARD:
            strategy_name = "HIGHEST REWARD";
            break;
        case STRATEGY_LOWEST_REWARD:
            strategy_name = "LOWEST REWARD";
            break;
        default:
            strategy_name = "RANDOM";
    }

    printf("MINER THREAD %ld USING STRATEGY: %s\n", miner_id, strategy_name);

    int shmid_pool = shmget(key_pool, 0, 0777);
    TransactionPool *transaction_pool = (TransactionPool *)shmat(shmid_pool, NULL, 0);
    
    sem_t *sem_pool = sem_open(SEM_POOL_NAME, 0);
    if (sem_pool == SEM_FAILED) {
        perror("ERROR OPENING POOL SEMAPHORE");
        pthread_exit(NULL);
    }

    int shmid_ledger = shmget(key_ledger, 0, 0777);
    if (shmid_ledger == -1) {
        perror("ERROR GETTING SHARED MEMORY ID FOR LEDGER");
        return 0;
    }
    BlockchainLedger *blockchain_ledger = (BlockchainLedger *)shmat(shmid_ledger, NULL, 0);
    if (blockchain_ledger == (void *)-1) {
        perror("ERROR ATTACHING TO SHARED MEMORY FOR LEDGER");
        return 0;
    }

    while(terminar == 0){
        snprintf(tag, sizeof(tag), "MINER%ld", miner_id);
        while (1) {
            sem_wait(sem_pool);
            if (transaction_pool->count >= config.transactions_per_block) {
                break;
            }
            sem_post(sem_pool);
            usleep(100000);
        }

        Block *new_block = malloc(sizeof(Block) + config.transactions_per_block * sizeof(Transaction));
        if (!new_block) {
            perror("FAILED TO ALLOCATE MEMORY FOR NEW BLOCK");
            sem_post(sem_pool);
            pthread_exit(NULL);
        }

        new_block->block_id = transaction_pool->current_block_id++;
        new_block->timestamp = time(NULL);
        new_block->miner_id = miner_id;

        int *selected_indices = malloc(transaction_pool->count * sizeof(int));
        if (!selected_indices) {
            perror("FAILED TO ALLOCATE MEMORY FOR SELECTED INDICES");
            free(new_block);
            sem_post(sem_pool);
            pthread_exit(NULL);
        }

        for (int i = 0; i < transaction_pool->count; i++) {
            selected_indices[i] = i;
            
        }

        if (strategy == STRATEGY_HIGHEST_REWARD) {
            // reward (highest first)
            for (int i = 0; i < transaction_pool->count - 1; i++) {
                for (int j = i + 1; j < transaction_pool->count; j++) {
                    if (transaction_pool->transactions[selected_indices[i]].reward < 
                        transaction_pool->transactions[selected_indices[j]].reward) {
                        int temp = selected_indices[i];
                        selected_indices[i] = selected_indices[j];
                        selected_indices[j] = temp;
                    }
                }
            }
        } else if (strategy == STRATEGY_LOWEST_REWARD) {
            // reward (lowest first)
            for (int i = 0; i < transaction_pool->count - 1; i++) {
                for (int j = i + 1; j < transaction_pool->count; j++) {
                    if (transaction_pool->transactions[selected_indices[i]].reward > 
                        transaction_pool->transactions[selected_indices[j]].reward) {
                        int temp = selected_indices[i];
                        selected_indices[i] = selected_indices[j];
                        selected_indices[j] = temp;
                    }
                }
            }
        } else { // STRATEGY_RANDOM
            for (int i = transaction_pool->count - 1; i > 0; i--) {
                int j = rand() % (i + 1);
                int temp = selected_indices[i];
                selected_indices[i] = selected_indices[j];
                selected_indices[j] = temp;
            }
        }

        int total_reward = 0;
        float total_value = 0;

        for (int i = 0; i < config.transactions_per_block; i++) {
            if(transaction_pool->transactions[selected_indices[i]].empty == 0){
                new_block->transactions[i] = transaction_pool->transactions[selected_indices[i]];
                total_reward += new_block->transactions[i].reward;
                total_value += new_block->transactions[i].value;
            }
        }
        /*
        for (int i = 0; i < config.transactions_per_block; i++) {
            int remove_idx = selected_indices[i];
            for (int j = 0; j < i; j++) {
                if (selected_indices[j] < remove_idx) {
                    remove_idx--;
                }
            }
            transaction_pool->transactions[remove_idx].empty = 1; 
            transaction_pool->count--;
        }
        */
        PoWResult r;
        do {
            new_block->timestamp = time(NULL);
            printf("COMPUTING THE POW WITH TIMESTAMP %ld\n", new_block->timestamp);
            r = proof_of_work(new_block);
        } while (r.error == 1);

        snprintf(message, sizeof(message), "NEW HASH: %s", r.hash);
        log_message(tag, message, log_file, sem);

        sem_wait(sem_ledger);
        if (blockchain_ledger->count == 0){
            strncpy(new_block->previous_block_hash, hash_buffer, HASH_SIZE);
        }
        else{
            strncpy(new_block->previous_block_hash, r.hash, HASH_SIZE);
        }
        print_block_info(new_block);

        r = proof_of_work(new_block);

        sem_post(sem_ledger);

        sem_post(sem_pool);

        int pipe_fd = open(VALIDATOR_PIPE, O_WRONLY);
        if (pipe_fd == -1) {
            perror("ERROR OPENING NAMED PIPE FOR WRITING");
            free(selected_indices);
            free(new_block);
            pthread_exit(NULL);
        }

        size_t block_size = sizeof(Block) + config.transactions_per_block * sizeof(Transaction);
        
        if (write(pipe_fd, new_block, block_size) == -1) {
            perror("ERROR WRITING BLOCK TO NAMED PIPE");
        } else {
            snprintf(message, sizeof(message), "SENT BLOCK %d TO VALIDATOR", new_block->block_id);
            log_message(tag, message, log_file, sem);
        }

        close(pipe_fd);

        snprintf(message, sizeof(message), "MINED BLOCK %d WITH %d TRANSACTIONS, TOTAL VALUE: %.2f, EARNED %d REWARDS", new_block->block_id, config.transactions_per_block, total_value, total_reward);
        log_message(tag, message, log_file, sem);

        free(selected_indices);
        free(new_block);
    }
    shmdt(transaction_pool);
    shmdt(blockchain_ledger);

    printf("MINER THREAD %ld HAS FINISHED MINING!\n", miner_id);
    snprintf(message, sizeof(message), "HAS FINISHED MINING!");
    log_message(tag, message, log_file, sem);

    pthread_exit(NULL);
}

// Função responsável por lançar as threads
void miner(int num_miners) {
    miners = malloc(num_miners * sizeof(pthread_t));

    if (miners == NULL) {
        perror("ERROR ALLOCATING MEMORY FOR MINERS");
        exit(EXIT_FAILURE);
    }
    long ids[num_miners];

    for (long i = 0; i < num_miners; i++) {
        ids[i] = i + 1;
        if (pthread_create(&miners[i], NULL, mine, &ids[i]) != 0) {
            perror("ERROR CREATING MINER THREAD");
            exit(EXIT_FAILURE);
        }
    }
    for (int i = 0; i < num_miners; i++) {
        pthread_join(miners[i], NULL);
    }

    free(miners);
}

// Função do validator
void validator() {
    char message[100];
    Config config;
    process_config(&config);

    int shmid_pool = shmget(key_pool, 0, 0777);
    if (shmid_pool == -1) {
        perror("ERROR GETTING SHARED MEMORY ID FOR POOL");
        exit(EXIT_FAILURE);
    }
    
    TransactionPool *transaction_pool = (TransactionPool *)shmat(shmid_pool, NULL, 0);
    if (transaction_pool == (void *)-1) {
        perror("ERROR ATTACHING TO SHARED MEMORY FOR POOL");
        exit(EXIT_FAILURE);
    }
    
    sem_t *sem_pool = sem_open(SEM_POOL_NAME, 0);
    if (sem_pool == SEM_FAILED) {
        perror("ERROR OPENING POOL SEMAPHORE");
        exit(EXIT_FAILURE);
    }

    int pipe_fd;
    
    pipe_fd = open(VALIDATOR_PIPE, O_RDONLY);
    if (pipe_fd == -1) {
        perror("ERROR OPENING NAMED PIPE FOR READING");
        exit(EXIT_FAILURE);
    }
    
    snprintf(message, sizeof(message), "STARTED AND WAITING FOR MINER DATA");
    log_message("VALIDATOR", message, log_file, sem);

    size_t block_buffer_size = sizeof(Block) + config.transactions_per_block * sizeof(Transaction);
    void *block_buffer = malloc(block_buffer_size);
    if (!block_buffer) {
        perror("FAILED TO ALLOCATE MEMORY FOR BLOCK BUFFER");
        exit(EXIT_FAILURE);
    }

    while(1) {
        ssize_t bytes_read = read(pipe_fd, block_buffer, block_buffer_size);
        if (bytes_read > 0) {
            Block *received_block = (Block *)block_buffer;
            
            int verify = 1;

            float total_value = 0;
            float total_reward = 0;

            sem_wait(sem_pool);

            for (int i = 0; i < config.pool_size; i++){
                if (transaction_pool->transactions[i].empty == 0){
                    transaction_pool->transactions[i].age++;                    
                }
                if (transaction_pool->transactions[i].age % 50 == 0){
                    transaction_pool->transactions[i].reward++;
                }
            }

            for (int i = 0; i < config.transactions_per_block; i++) {
                total_value += received_block->transactions[i].value;
                total_reward += received_block->transactions[i].reward;
                int found = 0;
                for (int j = 0; j < config.pool_size; j++){
                    if (transaction_pool->transactions[j].empty == 0 && received_block->transactions[i].transaction_id == transaction_pool->transactions[j].transaction_id){
                        found = 1;
                        break;
                    }
                }
                if (found == 0){
                    verify = 0;
                    break;
                }
            }

            if (verify){
                snprintf(message, sizeof(message), "RECEIVED BLOCK %d WITH %d TRANSACTIONS, TOTAL VALUE: %.2f, TOTAL REWARD: %.2f", received_block->block_id, config.transactions_per_block, total_value, total_reward);
                log_message("VALIDATOR", message, log_file, sem);
                if (!verify_nonce(received_block)) {
                    verify = 0;
                }
            }
            if (verify) {
                if (write_block_to_ledger(received_block)) {
                    for (int i = 0; i < config.transactions_per_block; i++) {
                        for (int j = 0; j < config.pool_size; j++){
                            if (transaction_pool->transactions[j].empty == 0 && received_block->transactions[i].transaction_id == transaction_pool->transactions[j].transaction_id){
                                transaction_pool->transactions[j].empty = 1;
                                transaction_pool->count--;
                                break;
                            }
                        }
                    }
                }
            }

            sem_post(sem_pool);
    
            MessageQueue val_msg;
            val_msg.verify = verify;
            val_msg.mtype = 1;
            val_msg.block_id = received_block->block_id;
            val_msg.miner_id = received_block->miner_id;
            val_msg.transaction_count = 10;
            val_msg.total_value = total_value;
            val_msg.total_reward = total_reward;


            long sum_delay = 0;
            for (int i = 0; i < config.transactions_per_block; i++) {
                sum_delay += (received_block->timestamp - received_block->transactions[i].timestamp);
            }
            val_msg.time_total = sum_delay;
            val_msg.time_count = config.transactions_per_block;
            
            if (msgsnd(msgq_id, &val_msg, sizeof(MessageQueue) - sizeof(long), 0) == -1) {
                perror("ERROR SENDING MESSAGE TO QUEUE");
            } else {
                snprintf(message, sizeof(message), "SENT BLOCK INFO TO STATISTICS");
                log_message("VALIDATOR", message, log_file, sem);
            }
        }
    }
    shmdt(transaction_pool);
    sem_close(sem_pool);
    close(pipe_fd);
    free(block_buffer);
}

// Função das estatisticas
void statistics() {

    signal(SIGUSR1, stats_sigusr1);

    char message[MESSAGE_SIZE];;
    MessageQueue val_msg;
    
    snprintf(message, sizeof(message), "STARTED AND WAITING FOR VALIDATOR DATA");
    log_message("STATISTICS", message, log_file, sem);
    
    while (1) {
        // Receber a mensagem
        if (msgrcv(msgq_id, &val_msg, sizeof(MessageQueue) - sizeof(long), 1, 0) == -1) {
            //perror("ERROR RECEIVING MESSAGE FROM QUEUE");
        } else {
            int miner_index = val_msg.miner_id - 1;
            if (val_msg.verify == 1) {
                snprintf(message, sizeof(message), "RECEIVED VALID BLOCK ID: %d (MINER ID : %d), TRANSACTIONS: %d, TOTAL VALUE: %.2f, TOTAL REWARD: %.2f", val_msg.block_id, val_msg.miner_id,  val_msg.transaction_count, val_msg.total_value, val_msg.total_reward);
                log_message("STATISTICS", message, log_file, sem);
                valid_miners[miner_index]++;
                credits_miners[miner_index] += val_msg.total_reward;
                blocks_count++;
            }
            else {
                snprintf(message, sizeof(message), "RECEIVED INVALID BLOCK ID: %d (MINER ID : %d), TRANSACTIONS: %d, TOTAL VALUE: %.2f, TOTAL REWARD: %.2f", val_msg.block_id, val_msg.miner_id,  val_msg.transaction_count, val_msg.total_value, val_msg.total_reward);
                log_message("STATISTICS", message, log_file, sem);
                invalid_miners[miner_index]++;
                blocks_count++;
            }
        }
        stats_sum_delay += val_msg.time_total;
        stats_count += val_msg.time_count;
    }
}