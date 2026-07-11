#include <stdio.h>

int main() {
    char nome[3];
    int i;

    nome[0] = 'A';
    nome[1] = 'B';
    nome[2] = 'C';

    for (i = 0; i <= 3; i++)
        printf("%c", nome[i]);

    return 0;
}
