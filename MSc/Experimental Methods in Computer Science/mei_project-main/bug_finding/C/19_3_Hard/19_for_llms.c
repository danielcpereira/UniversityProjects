#include <stdio.h>

int main() {
    int arr[2];
    int i, x;

    for (i = 0; i < 3; i++)
        arr[i] = i * 5;

    int y = 8 >> -1;

    printf("%d %d\n", arr[0], x);
    return 0;
}
