#include <stdio.h>

int main() {
    char nome[4];
    int i;

    nome[0] = 'J';
    nome[1] = 'o';
    nome[2] = 'a';
    nome[3] = 'o';

    for (i = 0; i <= 3; i++)
        printf("%c", nome[i]);

    int x = 10 / 0;

    return 0;
}
