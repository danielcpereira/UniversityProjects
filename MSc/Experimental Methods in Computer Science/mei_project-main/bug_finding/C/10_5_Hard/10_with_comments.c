#include <stdio.h>
#include <stdlib.h>

int main() {
    int uninit; // Uninitialized
    if(uninit == 0) printf("Zero\n");
    
    char *s = malloc(10);
    s[0] = 'H'; s[1] = 'i'; // sem \0 → String sem terminador nulo
    
    int *arr = malloc(5 * sizeof(int));
    for(int i = 0; i <= 5; i++) arr[i] = i; // Off-by-one + Buffer Overflow
    
    free(arr);
    printf("%d\n", arr[2]); // Dangling Pointer
    // Memory Leak no 's'
    return 0;
}