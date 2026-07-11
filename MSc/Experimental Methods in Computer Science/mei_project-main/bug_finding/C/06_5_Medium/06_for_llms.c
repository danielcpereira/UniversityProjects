#include <stdio.h>
#include <stdlib.h>

void leak() {
    int *x = malloc(100 * sizeof(int));
}

int main() {
    leak();
    int uninit;
    printf("Uninit: %d\n", uninit);
    
    char str[10];
    strncpy(str, "MuitoLongoString", 15);
    str[9] = '\0';
    
    int *p = malloc(sizeof(int));
    free(p);
    free(p);
    return 0;
}