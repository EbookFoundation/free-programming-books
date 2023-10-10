#include <stdio.h>
int main()
{
    int a, b, c;
    scanf("%d %d %d", &a, &b, &c);
    if (a > b)
    {
        if (a > c)
            printf("largest: %d\n", a);
        else
            printf("%d", c);
    }
    else
    {
        if (b > c)
            printf("largest :%d \n", b);
        else
            printf("%d", c);
    }
    return 0;
}
