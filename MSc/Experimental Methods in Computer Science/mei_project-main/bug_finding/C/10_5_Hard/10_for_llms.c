#include <stdio.h>
#include <stdlib.h>

int main() {
    int uninit;
    if(uninit == 0) printf("Zero\n");
    
    char *s = malloc(10);
    s[0] = 'H'; s[1] = 'i';
    
    int *arr = malloc(5 * sizeof(int));
    for(int i = 0; i <= 5; i++) arr[i] = i;
    
    free(arr);
    printf("%d\n", arr[2]);
    return 0;
}