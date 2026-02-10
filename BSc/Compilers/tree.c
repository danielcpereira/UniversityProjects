/*
Daniel Pereira Nº 2021237092
Manuel Couto   Nº 2021233121
*/

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <stdarg.h> 
#include "tree.h"
#include "y.tab.h"


int calculate_depth(node *node) {
    int contador = 1;
    list *irmao = node->sibling;

    while (irmao != NULL){
        contador++;
        irmao = irmao->next;
    }
    return contador;
}


node *new_node(char* category, char *token) {
    struct node *new = (struct node *)malloc(sizeof(struct node));

    new->category = strdup(category);

    if (token) {
        new->token= strdup(token);
    } else {
        new->token = NULL;
    }

    new->children = NULL; 
    new->sibling = NULL; 

    return new;
}

void add_childs(node *parent, int nargs, ...) {
    va_list args;                          
    va_start(args, nargs);                 

    for (int i = 0; i < nargs; i++) {
        node *child = va_arg(args, node *);
        
        
        list *new_list_node = (list *)malloc(sizeof(list));
        new_list_node->node = child;
        new_list_node->next = NULL;

        
        if (parent->children == NULL) {
            parent->children = new_list_node; 
        } else {
            list *current = parent->children;
            while (current->next != NULL) {
                current = current->next; 
            }
            current->next = new_list_node; 
        }
    }
    
    va_end(args);  
}

void add_sibling(node *sibling, node *new_sibling) {
    if (sibling == NULL || new_sibling == NULL) {
      
        return; 
    }

    list *current_sibling_list = sibling->sibling;

    if (current_sibling_list == NULL) {
        sibling->sibling = (list *)malloc(sizeof(list));
        sibling->sibling->node = new_sibling;
        sibling->sibling->next = NULL;
        
    } else {
        
        while (current_sibling_list->next != NULL) {
            current_sibling_list = current_sibling_list->next;
        }
        
        current_sibling_list->next = (list *)malloc(sizeof(list));
        current_sibling_list->next->node = new_sibling;
        current_sibling_list->next->next = NULL;
    }
}


void print_tree(node *node, int depth) {
    if (node == NULL) return; 

    for (int i = 0; i < depth; i++) {
        printf("..");
    }

    if (node->token != NULL) {
        printf("%s(%s)\n", node->category, node->token);
    } else {
        printf("%s\n", node->category);
    }

   
    list *current_child = node->children;
    while (current_child != NULL) {
        print_tree(current_child->node, depth + 1);
        current_child = current_child->next;
    }

    
    current_child = node->sibling;
    while (current_child != NULL) {
        print_tree(current_child->node, depth);
        current_child = current_child->next;
    }
}


void free_tree(node *node) {
    if (node == NULL) {
        return; 
    }

   
    list *current_child = node->children;
    while (current_child != NULL) {
        list *next_child = current_child->next; 
        free_tree(current_child->node); 
        free(current_child);
        current_child = next_child; 
    }

    
    current_child = node->sibling;
    while (current_child != NULL) {
        list *next_sibling = current_child->next; 
        free(current_child);
        current_child = next_sibling; 
    }

    free(node->category); 
    free(node->token); 
    free(node);
}


void update_type(node *parent, node *type) {
    if (parent == NULL || type == NULL) {
        return;
    }

    
    list *new_list_node = (list *)malloc(sizeof(list));
    new_list_node->node = type;
    new_list_node->next = parent->children;
    parent->children = new_list_node;

    
    list *current_sibling = parent->sibling;
    while (current_sibling != NULL) {
        update_type(current_sibling->node, type);
        current_sibling = current_sibling->next;
    }
}
