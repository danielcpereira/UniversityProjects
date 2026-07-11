#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main() {
    char *str = malloc(10);
    strcpy(str, "Test"); // Memory Leak + sem free()
    
    char dest[5];
    for(int i = 0; i <= 5; i++) // Off-by-one
        dest[i] = str[i]; // Buffer Overflow

    dest[4] = 'X'; // sem \0 garantido
    printf("%s\n", dest); // String sem terminador nulo
    
    int *p = NULL;
    free(p); // Undefined Behavior (free NULL nem sempre crasha, mas perigoso)
    return 0;
}