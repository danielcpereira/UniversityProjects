#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main() {
    char *str = malloc(10);
    strcpy(str, "Test");
    
    char dest[5];
    for(int i = 0; i <= 5; i++)
        dest[i] = str[i];

    dest[4] = 'X';
    printf("%s\n", dest);
    
    int *p = NULL;
    free(p);
    return 0;
}