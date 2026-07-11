#include <stdio.h>
#include <stdlib.h>

int main() {
    char *buf = malloc(20);
    buf[0] = 'A';
    // esqueceu \0 e free() → Memory Leak + String sem terminador
    
    int *dangling = malloc(sizeof(int));
    free(dangling);
    *dangling = 999; // Dangling Pointer
    
    int shift = 1 << 40; // Undefined Behavior (shift demasiado grande)
    printf("%d\n", shift);
    
    for(int i = 0; i <= 20; i++) // Off-by-one no buffer
        buf[i] = 'X';
    return 0;
}