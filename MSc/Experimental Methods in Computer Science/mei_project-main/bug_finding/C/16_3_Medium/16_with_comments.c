#include <stdio.h>

int main() {
    char nome[4];
    int i;

    nome[0] = 'J';
    nome[1] = 'o';
    nome[2] = 'a';
    nome[3] = 'o';          // BUG: falta '\0'

    for (i = 0; i <= 3; i++) // BUG: off-by-one
        printf("%c", nome[i]);

    int x = 10 / 0;         // BUG: divisão por zero

    return 0;
}
