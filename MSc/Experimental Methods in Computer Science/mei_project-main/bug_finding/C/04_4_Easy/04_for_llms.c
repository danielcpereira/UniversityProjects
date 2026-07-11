#include <stdio.h>
#include <stdlib.h>

int main() {
    int arr[10];
    int *p = arr;
    for(int i = 0; i < 12; i++)
        p[i] = i * 1000;

    int x;
    if(x > 0) printf("Positivo\n");

    char s[8] = "abcdef";
    s[7] = 'Z';
    printf("%s\n", s);
    return 0;
}