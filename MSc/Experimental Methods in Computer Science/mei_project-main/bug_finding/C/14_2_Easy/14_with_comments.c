#include <stdio.h>

int main() {
    char s[4];
    int i;

    s[0] = 'O';
    s[1] = 'l';
    s[2] = 'a';
    // BUG: falta '\0'

    for (i = 0; i <= 4; i++)  // BUG: off-by-one
        printf("%c", s[i]);

    return 0;
}
