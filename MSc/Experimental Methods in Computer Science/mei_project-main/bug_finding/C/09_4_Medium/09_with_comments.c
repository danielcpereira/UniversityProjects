#include <stdio.h>
#include <stdlib.h>

int main() {
    int *p = malloc(sizeof(int) * 10);
    int *q = p + 15; // Buffer Overflow via pointer arithmetic
    
    *q = 42; // Escrever fora dos limites
    
    free(p);
    int val = *p; // Dangling Pointer após free
    
    char str[5];
    for(int i = 0; i < 6; i++) str[i] = 'A'; // Off-by-one + sem \0
    printf("%s\n", str);
    return 0;
}