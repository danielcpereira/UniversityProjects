// Daniel Coelho Pereira 2021237092
// Eduardo Luís Pereira Marques 2022231584

#ifndef CONTROLLER_H
#define CONTROLLER_H

#include "utils.h"
#include <pthread.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <sys/msg.h>

extern pthread_t *miners;

// Function prototypes specific to controller
void *validators_ctrl();
void *mine(void *arg);
void miner(int num_miners);
void validator();
void statistics();
void termina();
int write_block_to_ledger(Block *block);
void print_block_info(Block *block);
void dump_ledger();
void print_miner_stats();
void stats_sigusr1(int sig);
void handle_sigusr1(int sig);
void *validators_ctrl();

#endif /* CONTROLLER_H */