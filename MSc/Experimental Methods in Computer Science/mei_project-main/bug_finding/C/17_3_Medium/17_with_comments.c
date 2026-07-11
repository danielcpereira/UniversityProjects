#include <stdio.h>
#include <limits.h>

int main() {
    int arr[3];
    int soma;                 // BUG: variável não inicializada
    int i;

    for (i = 0; i <= 3; i++)  // BUG: off-by-one
        arr[i] = i;

    int x = INT_MAX + 1;      // BUG: overflow de int

    printf("%d %d\n", soma, x);
    return 0;
}
