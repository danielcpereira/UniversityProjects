#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main() {
    int *arr = malloc(5 * sizeof(int)); // Memory Leak
    int x; // Uninitialized variable
    printf("Valor: %d\n", x); 

    for(int i = 0; i <= 5; i++) { // Off-by-one (i<=5)
        arr[i] = i * 10; // Buffer Overflow
    }

    char buf[10];
    strcpy(buf, "HelloWorldExtra"); // Buffer Overflow + sem \0 garantido
    printf("%s\n", buf);
    return 0;
}