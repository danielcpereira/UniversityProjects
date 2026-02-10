/*
Daniel Pereira Nº 2021237092
Manuel Couto   Nº 2021233121
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "symbol_table.h"
#include "tree.h"
#define INITIAL_CAPACITY 10000

int num = 0;
char var[10000] = "";
int flag = 0;
int flag2 = 0;
int flag3 = 0;

typedef struct {
    char *function_name;
    symbol_table *table;
} function_symbol_table;

function_symbol_table function_tables[100000];
int function_table_count = 0;

char* lowerCase(char* string) {
    char* stringLower = (char*)malloc(strlen(string) + 1);
    strcpy(stringLower, string);
    if (stringLower[0] >= 'A' && stringLower[0] <= 'Z') {
        stringLower[0] += 32;
    }
    return stringLower;
}

symbol_table* create_symbol_table() {
    symbol_table *table = (symbol_table *)malloc(sizeof(symbol_table));
    table->entries = (symbol_entry **)malloc(sizeof(symbol_entry *) * INITIAL_CAPACITY);
    table->size = 0;
    table->capacity = INITIAL_CAPACITY;
    return table;
}

void add_symbol(symbol_table *table, char *name, char *type, char *category) {
    if (name == NULL || name[0] == '\0') {
        return;
    }

    for (int i = 0; i < table->size; i++) {
        if (strcmp(table->entries[i]->name, name) == 0 &&
            strcmp(table->entries[i]->type, type) == 0 &&
            strcmp(table->entries[i]->category, category) == 0) {
            
            return;
        }
    }

    if (table->size >= table->capacity) {
        table->capacity *= 2;
        table->entries = (symbol_entry **)realloc(table->entries, sizeof(symbol_entry *) * table->capacity);
    }

    symbol_entry *entry = (symbol_entry *)malloc(sizeof(symbol_entry));
    entry->name = strdup(name);
    entry->type = strdup(type);
    entry->category = strdup(category);
    table->entries[table->size++] = entry;
}


void print_symbol_table(symbol_table *table, char *title) {
    printf("===== %s =====\n", title);

    for (int i = 0; i < table->size; i++) {
        if (strcmp(title, "Global Symbol Table") == 0 ){
             printf("%s\t%s", table->entries[i]->name, table->entries[i]->type);
             if(strcmp(table->entries[i]->category, "None") != 0 ){
                printf("\t%s",table->entries[i]->category);
             }
             printf("\n");
        }
        else{
            printf("%s\t\t%s", table->entries[i]->name, table->entries[i]->type);
            if(strcmp(table->entries[i]->category, "None") != 0 ){
                printf("\t%s",table->entries[i]->category);
            }
            printf("\n");
        } 
    }
    printf("\n");
}

void free_symbol_table(symbol_table *table) {
    for (int i = 0; i < table->size; i++) {
        free(table->entries[i]->name);
        free(table->entries[i]->type);
        free(table->entries[i]->category);
        free(table->entries[i]);
    }
    free(table->entries);
    free(table);
}

symbol_table *current_func_table = NULL; 

void register_symbols(node *n, symbol_table *table) {
    
    if (n == NULL) {
        return;
    }
    
    if (strcmp(n->category, "VarDecl") == 0) {
        list *var_list = n->children->next; 

    while (var_list != NULL) {
        node *var_node = var_list->node; 

        if (num == 1) {
            if (current_func_table) {
                int exists = 0;
                for (int i = 0; i < current_func_table->size; i++) {
                    if (strcmp(current_func_table->entries[i]->name, var_node->token) == 0) {
                        exists = 1;
                        break;
                    }
                }
                if (!exists) {
                    add_symbol(current_func_table, var_node->token, lowerCase(n->children->node->category), "");
                }
            }
        } else if (num == 0) {
            int exists = 0;
            for (int i = 0; i < table->size; i++) {
                if (strcmp(table->entries[i]->name, var_node->token) == 0) {
                    exists = 1;
                    break;
                }
            }
            if (!exists) {
                add_symbol(table, var_node->token, "", lowerCase(n->children->node->category));
            }
        }

        var_list = var_list->next; 
    }

    if ( n->sibling == NULL){
         flag = 0;
         
    }
}

    if ( strcmp(n->category, "Return") == 0) {
        flag = 0;
        num = 0;
        flag2= 0;
        current_func_table = NULL;


    }

    if (strcmp(n->category, "FuncBody") == 0){
        if(!n->children->node){
           
            current_func_table = NULL;
            flag = 0;
            num = 0;
        }
    }
    
    if (strcmp(n->category, "FuncHeader") == 0) {

        char *func_name = n->children->node->token;
        char type1[10000] = "";
        
        char category[10000] = "";
     
        num = 1;
        
       
        if (strcmp(lowerCase(n->children->next->node->category), "funcParams") == 0) {
            
            strcpy(category, "none");
        }
        else{
            
            flag = 1;
            
            sprintf(category, "%s", lowerCase(n->children->next->node->category));
            
        }
        
        node *aux;
    
        if(flag){
            if  (n != NULL && n->children != NULL && n->children->next != NULL &&
                n->children->next->next != NULL && n->children->next->next->node != NULL &&
                n->children->next->next->node->children != NULL && 
                n->children->next->next->node->children->node != NULL) {
                aux = n->children->next->next->node->children->node;


                if (aux->children != NULL && aux->children->node != NULL) {
                    strcat(type1, lowerCase(aux->children->node->category));
                }

                if(n->children->next->next->node->children->next->node){
                    aux = n->children->next->next->node->children->next->node;
                    strcat(type1, ",");
                    strcat(type1, lowerCase(aux->children->node->category));
                
                }

                if(aux->sibling){
                    aux = aux->sibling->node;
                    
                    }
                else{

                    aux = NULL;
                    }

                while(aux){
                    strcat(type1, ",");
                    strcat(type1, lowerCase(aux->children->node->category));
                    if(aux->sibling){aux = aux->sibling->node;}
                    else{aux = NULL;}
                }
            }
        }else{
            if (n != NULL && n->children != NULL && n->children->next != NULL &&
                n->children->next->node != NULL && n->children->next->node->children != NULL &&
                n->children->next->node->children->node != NULL) {

                aux = n->children->next->node->children->node;
                
                if (aux->children != NULL && aux->children->node != NULL) {
                    strcat(type1, lowerCase(aux->children->node->category));
                }
                if(n->children->next->node->children->next->node){
                    aux = n->children->next->node->children->next->node;
                    strcat(type1, ",");
                    strcat(type1, lowerCase(aux->children->node->category));
                
                }
                if(aux->sibling){
                    aux = aux->sibling->node;
                    }
                else{
                    aux = NULL;
                    }
                while(aux){
                    strcat(type1, ",");
                    strcat(type1, lowerCase(aux->children->node->category));
                    if(aux->sibling){aux = aux->sibling->node;}
                    else{aux = NULL;}
                }
            }
        }
        

        char type[20000];
        sprintf(type, "(%s)", type1);

        if (strcmp(type, "(funcParams)") == 0) {
            strcpy(type, "()");
        }

        
        
        int exists = 0;
        for (int i = 0; i < table->size; i++) {
            if (strcmp(table->entries[i]->name, func_name) == 0) {
                exists = 1;
                break;
            }
        }

        if (exists) {
            return;
        }

        add_symbol(table, func_name, type, category);

        current_func_table = create_symbol_table(); 
        char *func_title = (char *)malloc( sizeof(func_name)+sizeof(type)+100);
        sprintf(func_title, "Function %s%s Symbol Table", func_name, type);

        add_symbol(current_func_table, "return", category,"None");
        function_tables[function_table_count].function_name = func_title;
        function_tables[function_table_count].table = current_func_table;
        function_table_count++;
    }
    
    if (strcmp(n->category, "ParamDecl") == 0) {
        if (current_func_table) { 
            add_symbol(current_func_table, n->children->next->node->token, lowerCase(n->children->node->category), "param");
        }
    }
    
    list *child = n->children;
    while (child != NULL) {
        register_symbols(child->node, table);
        child = child->next;
    }
    
    
    list *sibling = n->sibling;
    while (sibling != NULL) {
        register_symbols(sibling->node, table);
        sibling = sibling->next;
    }

    
    if (strcmp(n->category, "FuncDecl") == 0) {
        current_func_table = NULL;
    }
}


void print_all_tables(symbol_table *global_table) {
    print_symbol_table(global_table, "Global Symbol Table");

    for (int i = 0; i < function_table_count; i++) {
        print_symbol_table(function_tables[i].table, function_tables[i].function_name);
    }
}



