#include <stdio.h>

int main() {
    char s[4];
    int i;

    s[0] = 'O';
    s[1] = 'l';
    s[2] = 'a';

    for (i = 0; i <= 4; i++)
        printf("%c", s[i]);

    return 0;
}
