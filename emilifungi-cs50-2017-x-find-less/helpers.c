/**
 * helpers.c
 *
 * Helper functions for Problem Set 3.
 */
 
#include <cs50.h>

#include "helpers.h"

/**
 * Returns true if value is in array of n values, else false.
 */

bool search(int value, int values[], int n)
{
    // TODO: implement a searching algorithm
    
    int start = 0;
    int end = n;
    
    while (end >= start)
    {
        int middle = (start + end) / 2;
        
        if (values[middle] == value)
        {
            return true;
        }
        
        else if (value < values[middle])
        {
            end = middle - 1;
        }
        
        else if (value > values[middle])
        {
            start = middle + 1;
        }
    }
    return false;
}

/**
 * Sorts array of n values.
 */

void sort(int values[], int n)
{
    int c = -1;
    int i = 0;
    int temp;
    
    while (c != 0)
    {
        
        c = 0;
       
       for (i = 0; i < n; i++)
       {
           
            if (values[i] > values[i + 1])
            {
                c++;
                temp = values[i];
                values[i] = values[i + 1];
                values[i + 1] = temp;
            }
            
       }
       
    }
  
    return;
}
