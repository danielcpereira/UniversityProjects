#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main() {
    char *data = malloc(16);
    strcpy(data, "BufferOverflowTest");
    
    char dest[8];
    memcpy(dest, data, 16);
    
    int x;
    int y = x / 0;
    
    free(data);
    free(data);
    return 0;
}