#include <stdio.h>
#include <stdlib.h>

int main() {
    int *p = malloc(sizeof(int) * 10);
    int *q = p + 15;
    
    *q = 42;
    
    free(p);
    int val = *p;
    
    char str[5];
    for(int i = 0; i < 6; i++) str[i] = 'A';
    printf("%s\n", str);
    return 0;
}