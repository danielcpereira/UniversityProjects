#include <stdio.h>
#include <stdlib.h>

int main() {
    char *buf = malloc(20);
    buf[0] = 'A';
    
    int *dangling = malloc(sizeof(int));
    free(dangling);
    *dangling = 999;
    
    int shift = 1 << 40;
    printf("%d\n", shift);
    
    for(int i = 0; i <= 20; i++)
        buf[i] = 'X';
    return 0;
}