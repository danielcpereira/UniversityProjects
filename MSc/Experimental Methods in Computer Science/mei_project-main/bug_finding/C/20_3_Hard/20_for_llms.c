#include <stdio.h>
#include <stdlib.h>

int main() {
    int *p = malloc(2 * sizeof(int));
    int *q;

    p[0] = 1;
    p[1] = 2;

    q = p;
    free(p);

    q[2] = 10;

    int *x = malloc(10);

    return 0;
}
