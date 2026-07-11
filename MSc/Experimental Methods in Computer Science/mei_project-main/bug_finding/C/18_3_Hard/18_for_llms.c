#include <stdio.h>
#include <stdlib.h>

int main() {
    int *p = malloc(sizeof(int));
    int x;

    *p = 10;
    free(p);
    free(p);

    printf("%d\n", *p);

    printf("%d\n", x);
    return 0;
}
