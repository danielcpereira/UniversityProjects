#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main() {
    char *data = malloc(16);
    strcpy(data, "BufferOverflowTest"); // Buffer Overflow + Memory Leak
    
    char dest[8];
    memcpy(dest, data, 16); // Buffer Overflow
    
    int x; // Uninitialized
    int y = x / 0; // Division by zero (UB)
    
    free(data);
    free(data); // Double Free
    return 0;
}