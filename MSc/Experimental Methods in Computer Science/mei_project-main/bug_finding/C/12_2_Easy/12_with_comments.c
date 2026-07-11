#include <stdio.h>

int main() {
    char nome[3];
    int i;

    nome[0] = 'A';
    nome[1] = 'B';
    nome[2] = 'C';        // BUG: falta '\0'

    for (i = 0; i <= 3; i++)  // BUG: off-by-one
        printf("%c", nome[i]);

    return 0;
}
