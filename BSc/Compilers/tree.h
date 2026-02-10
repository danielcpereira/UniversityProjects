/*
Daniel Pereira N 2021237092
Manuel Couto   N 2021233121
*/

#ifndef TREE_H
#define TREE_H

typedef struct node node;
typedef struct node_list list;

struct node {
    char *category;
    char *token;
    list *children;
    list *sibling;
};

struct node_list {
    node *node;
    list *next;
};

node *new_node(char *category, char *token);
void add_childs(node *parent,int nargs, ...);
void add_sibling(node *sibling, node *new_sibling);
void print_tree(struct node *node, int depth);
int calculate_depth(node *node);
void free_tree(node *node);
void update_type(node *parent, node *type);
#endif