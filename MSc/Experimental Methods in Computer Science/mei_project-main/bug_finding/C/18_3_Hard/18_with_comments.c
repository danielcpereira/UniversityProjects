#include <stdio.h>
#include <stdlib.h>

int main() {
    int *p = malloc(sizeof(int));
    int x;                   // BUG: variável não inicializada

    *p = 10;
    free(p);
    free(p);                 // BUG: double free

    printf("%d\n", *p);      // BUG: dangling pointer

    printf("%d\n", x);
    return 0;
}
