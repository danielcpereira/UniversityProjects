#include <stdio.h>
#include <stdlib.h>

void process(int *p) {
    free(p);
    *p = 42;
}

int main() {
    int *ptr = malloc(sizeof(int));
    *ptr = 10;
    process(ptr);
    free(ptr);
    int sum = 0;
    for(int i = 0; i < 100000; i++) sum += i;
    printf("%d\n", sum);
    return 0;
}