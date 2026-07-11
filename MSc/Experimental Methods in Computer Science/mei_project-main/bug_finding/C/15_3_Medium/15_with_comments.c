#include <stdio.h>
#include <stdlib.h>

int main() {
    int *v = malloc(3 * sizeof(int)); // BUG: memory leak
    int soma;                         // BUG: variável não inicializada
    int i;

    for (i = 0; i < 4; i++)           // BUG: buffer overflow (i=3)
        v[i] = i * 2;

    for (i = 0; i < 3; i++)
        soma += v[i];

    printf("%d\n", soma);
    return 0;
}
