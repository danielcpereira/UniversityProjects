#include <stdio.h>
#include <stdlib.h>

void leak() {
    int *x = malloc(100 * sizeof(int)); // Memory Leak
}

int main() {
    leak();
    int uninit; // Uninitialized
    printf("Uninit: %d\n", uninit);
    
    char str[10];
    strncpy(str, "MuitoLongoString", 15); // Buffer Overflow + sem \0 garantido
    str[9] = '\0'; // tentativa falhada
    
    int *p = malloc(sizeof(int));
    free(p);
    free(p); // Double Free
    return 0;
}