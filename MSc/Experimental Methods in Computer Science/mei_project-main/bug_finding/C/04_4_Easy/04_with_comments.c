#include <stdio.h>
#include <stdlib.h>

int main() {
    int arr[10];
    int *p = arr;
    for(int i = 0; i < 12; i++) // Off-by-one + Buffer Overflow
        p[i] = i * 1000;

    int x; // Uninitialized
    if(x > 0) printf("Positivo\n"); // Bug

    char s[8] = "abcdef"; // 6 chars + \0 = 7, mas...
    s[7] = 'Z'; // Overflow + corrompe memória
    printf("%s\n", s);
    return 0;
}