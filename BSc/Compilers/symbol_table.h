/*
Daniel Pereira N 2021237092
Manuel Couto   N 2021233121
*/
#ifndef SYMBOL_TABLE_H
#define SYMBOL_TABLE_H

#include "tree.h"  

typedef struct symbol_entry {
    char *name;        
    char *type;        
    char *category;    
} symbol_entry;

typedef struct symbol_table {
    symbol_entry **entries;   
    int size;                 
    int capacity;             
} symbol_table;

symbol_table* create_symbol_table();
char* lowerCase(char* string);
void add_symbol(symbol_table *table, char *name, char *type, char *category);
void print_symbol_table(symbol_table *table, char *title);
void free_symbol_table(symbol_table *table);

void register_symbols(node *n, symbol_table *table);
void print_all_tables(symbol_table *global_table);



#endif
