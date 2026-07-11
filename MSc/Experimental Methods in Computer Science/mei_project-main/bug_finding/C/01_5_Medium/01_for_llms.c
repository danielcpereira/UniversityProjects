#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main() {
    int *arr = malloc(5 * sizeof(int));
    int x;
    printf("Valor: %d\n", x);

    for(int i = 0; i <= 5; i++) {
        arr[i] = i * 10;
    }

    char buf[10];
    strcpy(buf, "HelloWorldExtra");
    printf("%s\n", buf);
    return 0;
}