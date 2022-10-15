#include<stdio.h>
void main()
{
    int n,i,ctr=0,j;
    printf("enter numbers of elements");
    scanf("%d",&n);
    int arr[n];
    printf("enter your elements");
    for(i=0 ; i<n ; i++)
    {
        scanf("%d",&arr[i]);
    }
    for(i=0 ; i<n ; i++)
    {
        for(j=i+1 ; j<n ; j++)
        {
            if(arr[i]==arr[j])
            {
                ctr++;
                break;
            }
        }
    }
    printf("%d",ctr);
}      
