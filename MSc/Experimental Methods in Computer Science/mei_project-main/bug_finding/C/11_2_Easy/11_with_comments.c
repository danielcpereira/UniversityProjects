#include <stdio.h>

int main() {
    int arr[4];
    int soma;                 // BUG: variável não inicializada
    int i;

    for (i = 0; i <= 4; i++) { // BUG: off-by-one (acede arr[4])
        arr[i] = i * 2;
    }

    printf("Soma = %d\n", soma);
    return 0;
}
