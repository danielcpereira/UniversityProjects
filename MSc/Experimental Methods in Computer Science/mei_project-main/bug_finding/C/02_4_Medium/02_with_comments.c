#include <stdio.h>
#include <stdlib.h>

void process(int *p) {
    free(p); // Double Free possível
    *p = 42; // Dangling Pointer
}

int main() {
    int *ptr = malloc(sizeof(int));
    *ptr = 10;
    process(ptr);
    free(ptr); // Double Free
    int sum = 0;
    for(int i = 0; i < 100000; i++) sum += i; // Integer Overflow provável
    printf("%d\n", sum);
    return 0;
}