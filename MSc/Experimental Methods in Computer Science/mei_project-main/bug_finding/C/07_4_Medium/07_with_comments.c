#include <stdio.h>

int main() {
    int arr[5] = {0};
    for(int i = 0; i < 6; i++) // Off-by-one
        arr[i] = i * 1000000; // Integer Overflow provável em alguns sistemas

    char *s = "Test";
    char copy[4];
    strcpy(copy, s); // Buffer Overflow (4 bytes para 5 com \0)
    
    int *ptr = NULL;
    printf("%d\n", *ptr); // Undefined Behavior (dereference NULL)
    return 0;
}