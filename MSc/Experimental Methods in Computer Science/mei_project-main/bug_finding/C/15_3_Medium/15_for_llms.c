#include <stdio.h>
#include <stdlib.h>

int main() {
    int *v = malloc(3 * sizeof(int));
    int soma;
    int i;

    for (i = 0; i < 4; i++)
        v[i] = i * 2;

    for (i = 0; i < 3; i++)
        soma += v[i];

    printf("%d\n", soma);
    return 0;
}
