#include <stdio.h>
#include <limits.h>

int main() {
    int arr[3];
    int soma;
    int i;

    for (i = 0; i <= 3; i++)
        arr[i] = i;

    int x = INT_MAX + 1;
    
    printf("%d %d\n", soma, x);
    return 0;
}
