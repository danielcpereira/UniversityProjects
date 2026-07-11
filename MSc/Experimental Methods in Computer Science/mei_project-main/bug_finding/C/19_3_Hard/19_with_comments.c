#include <stdio.h>

int main() {
    int arr[2];
    int i, x;                // BUG: x não inicializado

    for (i = 0; i < 3; i++)  // BUG: buffer overflow (i=2)
        arr[i] = i * 5;

    int y = 8 >> -1;         // BUG: shift negativo (undefined)

    printf("%d %d\n", arr[0], x);
    return 0;
}
