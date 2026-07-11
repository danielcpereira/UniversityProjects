#include <stdio.h>
#include <limits.h>

int main() {
    int x;                   // BUG: variável não inicializada
    int y = INT_MAX + 50;    // BUG: overflow de int (undefined)

    printf("%d %d\n", x, y);
    return 0;
}
