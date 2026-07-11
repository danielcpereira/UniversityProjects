#include <stdio.h>

int main() {
    int arr[5] = {0};
    for(int i = 0; i < 6; i++)
        arr[i] = i * 1000000;

    char *s = "Test";
    char copy[4];
    strcpy(copy, s);
    
    int *ptr = NULL;
    printf("%d\n", *ptr);
    return 0;
}