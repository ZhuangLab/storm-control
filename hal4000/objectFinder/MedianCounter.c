/*
 * @file
 *
 * Object finding code based on using the median background 
 * subtraction and threshold object detection.
 * 
 * Hazen 3/09
 * 
 * Linux:
 *  gcc -fPIC -g -c -Wall MedianCounter.c
 *  gcc -shared -Wl,-soname,MedianCounter.so.1 -o MedianCounter.so.1.0.1 MedianCounter.o -lc
 *
 * Windows:
 *  gcc -c MedianCounter.c
 *  gcc -shared -o MedianCounter.dll MedianCounter.o
 */

/* Include */

#include <stdlib.h>
#include <stdio.h>
#include <math.h>


/* Function Declarations */

short quick_select(short [], int);
void mean_dev(short [], short, int*, int*);
void image_median_mean_dev(short [], short [], float [], float [], int, int, int);
void threshold_image(short [], short [], int, int, int, float);
void remove_object(short [], int, int, int*, int, int);
int number_objects(short [], int, int, int, float);
void find_and_remove_object(short [], int, int, int *, int, int, int, int, int *, int *, int *);
void number_and_loc_objects(short [], int, int, int, float, float [], float [], int *);


/* Functions */

/*
 *  This Quickselect routine is based on the algorithm described in
 *  "Numerical recipes in C", Second Edition,
 *  Cambridge University Press, 1992, Section 8.5, ISBN 0-521-43108-5
 *  This code by Nicolas Devillard - 1998. Public domain.
 */

#define ELEM_SWAP(a,b) { register short t=(a);(a)=(b);(b)=t; }

/*
 * arr[] : array of short integers
 * n : number of elements in arr[].
 *
 * returns : median of arr[].
 *
 * Note that this modifies the input array.
 */

short quick_select(short arr[], int n) 
{
    int low, high ;
    int median;
    int middle, ll, hh;

    low = 0 ; high = n-1 ; median = (low + high) / 2;
    for (;;) {
        if (high <= low) /* One element only */
            return arr[median] ;

        if (high == low + 1) {  /* Two elements only */
            if (arr[low] > arr[high])
                ELEM_SWAP(arr[low], arr[high]) ;
            return arr[median] ;
        }

    /* Find median of low, middle and high items; swap into position low */
    middle = (low + high) / 2;
    if (arr[middle] > arr[high])    ELEM_SWAP(arr[middle], arr[high]) ;
    if (arr[low] > arr[high])       ELEM_SWAP(arr[low], arr[high]) ;
    if (arr[middle] > arr[low])     ELEM_SWAP(arr[middle], arr[low]) ;

    /* Swap low item (now in position middle) into position (low+1) */
    ELEM_SWAP(arr[middle], arr[low+1]) ;

    /* Nibble from each end towards middle, swapping items when stuck */
    ll = low + 1;
    hh = high;
    for (;;) {
        do ll++; while (arr[low] > arr[ll]) ;
        do hh--; while (arr[hh]  > arr[low]) ;

        if (hh < ll)
        break;

        ELEM_SWAP(arr[ll], arr[hh]) ;
    }

    /* Swap middle item (in position low) back into correct position */
    ELEM_SWAP(arr[low], arr[hh]) ;

    /* Re-set active partition */
    if (hh <= median)
        low = ll;
        if (hh >= median)
        high = hh - 1;
    }
}

#undef ELEM_SWAP


/*
 * Computes the mean and variance of an array.
 *
 * arr[] : array of short integers.
 * n : number of elements in arr[].
 * *mean : set to the mean of arr[].
 * *variance : set to the variance of arr[].
 *
 * returns : nothing.
 *
 */

void mean_var(short arr[], int n, float *mean, float *variance)
{
  int i, t1, t2;

  t1 = 0;
  t2 = 0;
  for(i=0;i<n;i++){
    t1 += arr[i];
    t2 += arr[i] * arr[i];
  }
  *mean = ((float)t1)/((float)n);
  *variance = ((float)t2)/((float)n) - (*mean * *mean);
}


/*
 * Computes the median, mean and standard deviation of each cell in an image.
 *
 * arr[] : array of short integers representing an image.
 * median[] : set to the median of each cell in the image (must be pre-allocated).
 * mean[] : set to the mean of each cell in the image (must be pre-allocated).
 * dev[] : set to the standard deviation of each cell in the image (must be pre-allocated).
 * size_x : the size of the x dimension of the image.
 * size_y : the size of the y dimension of the image.
 * cell_size : the size of a single cell in which to compute the stats.
 *
 * returns : nothing.
 */

void image_median_mean_dev(short arr[], short median[], float mean[], float dev[], int size_x, int size_y, int cell_size)
{
  int i, j, k, l, m, t1, t2, t3, number_cells_x, number_cells_y;
  float tm, tv;
  short *working_array;

  working_array = (short *)malloc(sizeof(short) * cell_size * cell_size);
  /* if (!((size % cell_size) == 0)) printf("size is not a multiple of cell_size!\n"); */
  number_cells_x = size_x/cell_size;
  number_cells_y = size_y/cell_size;
  for (i=0;i<number_cells_y;i++){
    t1 = i * cell_size;
    for (j=0;j<number_cells_x;j++){
      t2 = j * cell_size;
      m = 0;
      for (k=0;k<cell_size;k++){
	t3 = (t1 + k)*size_x;
	for (l=0;l<cell_size;l++){
	  working_array[m] = arr[t3 + t2 + l];
	  m++;
	}
      }
      median[i * number_cells_x + j] = quick_select(working_array, cell_size * cell_size);
      mean_var(working_array, cell_size * cell_size, &tm, &tv);
      mean[i * number_cells_x + j] = tm;
      dev[i * number_cells_x + j] = sqrt(tv);
    }
  }
  free(working_array);
}


/*
 * Thresholds an image based on the median and the threshold.
 *
 * image[] : array of short integers representing an image.
 * t_image[] : pre-allocated array of short integers to store the thresholded image.
 * size_x : the size of the x dimension of the image.
 * size_y : the size of the y dimension of the image.
 * cell_size : the size of a single cell in which to compute the stats, size should be a
 *             multiple of cell_size.
 * threshold : number of sigma above background to be a point in an object.
 *
 * returns : nothing.
 */

void threshold_image(short image[], short t_image[], int size_x, int size_y, int cell_size, float threshold)
{
  short thresh, *median;
  int i, j, k, l, t1, t2, t3, number_cells_x, number_cells_y;
  float *mean, *dev;

  number_cells_x = size_x/cell_size;
  number_cells_y = size_y/cell_size;
  median = (short *)malloc(sizeof(short) * number_cells_x * number_cells_y);
  mean = (float *)malloc(sizeof(float) * number_cells_x * number_cells_y);
  dev = (float *)malloc(sizeof(float) * number_cells_x * number_cells_y);
  image_median_mean_dev(image, median, mean, dev, size_x, size_y, cell_size);
  for (i=0;i<number_cells_y;i++){
    t1 = i * cell_size;
    for (j=0;j<number_cells_x;j++){
      t2 = j * cell_size;
      thresh = median[i * number_cells_x + j] + (short)threshold;
      for (k=0;k<cell_size;k++){
	t3 = (t1 + k)*size_x;
	for (l=0;l<cell_size;l++){
	  if (image[t3 + t2 + l] > thresh){
	    t_image[t3 + t2 + l] = image[t3 + t2 + l];
	  } else {
	    t_image[t3 + t2 + l] = 0;
	  }
	}
      }
    }
  }
  free(median);
  free(mean);
  free(dev);
}



/*
 * Removes contiguous objects from the thresholded image.
 *
 * t_image[] : the thresholded image.
 * t_size_x : size of the thresholded image.
 * t_size_y : size of the thresholded image.
 * o_size : pointer to storage for the number of elements in the object
 *          that were above the threshold.
 * i : current "y" location in the image.
 * j : current "x" location in the image.
 */

void remove_object(short t_image[], int t_size_x, int t_size_y, int *o_size, int i, int j)
{
  *o_size += 1;
  t_image[i*t_size_x + j] = 0;
  if (i>0){
    if (t_image[(i-1) * t_size_x + j] > 0){
      remove_object(t_image, t_size_x, t_size_y, o_size, i-1, j);
    }
  }
  if (i<(t_size_y-1)){
    if (t_image[(i+1) * t_size_x + j] > 0){
      remove_object(t_image, t_size_x, t_size_y, o_size, i+1, j);
    }
  }
  if (j>0){
    if (t_image[i * t_size_x + (j-1)] > 0){
      remove_object(t_image, t_size_x, t_size_y, o_size, i, j-1);
    }
  }
  if (j<(t_size_x-1)){
    if (t_image[i * t_size_x + (j+1)] > 0){
      remove_object(t_image, t_size_x, t_size_y, o_size, i, j+1);
    }
  }
}


/*
 * Counts the number of contiguous objects above threshold in the image.
 *
 * image[] : array of short integers representing an image.
 * size_x : the size of the x dimension of the image.
 * size_y : the size of the y dimension of the image.
 * cell_size : the size of a single cell in which to compute the stats, size should be a
 *             multiple of cell_size.
 * threshold : number of sigma above background to be a point in an object.
 *
 * returns : number of points above the threshold.
 */

int number_objects(short image[], int size_x, int size_y, int cell_size, float threshold)
{
  short *t_image;
  int i, j, t1, n_objects, o_size;

  t_image = (short *)malloc(sizeof(short) * size_x * size_y);
  threshold_image(image, t_image, size_x, size_y, cell_size, threshold);
  n_objects = 0;
  for(i=0;i<((size_y/cell_size)*cell_size);i++){
    t1 = i * size_x;
    for(j=0;j<((size_x/cell_size)*cell_size);j++){
      if (t_image[t1 + j] > 0){
	o_size = 1;
	remove_object(t_image, size_x, size_y, &o_size, i, j);
	if(o_size > 2){
	  n_objects++;
	}
      }
    }
  }
  free(t_image);

  return n_objects;
}


/*
 * Find the center of mass of contiguous objects and 
 * removes them from the thresholded image.
 *
 * t_image[] : the thresholded image.
 * t_size_x : size of the thresholded image in x.
 * t_size_y : size of the thresholded image in y.
 * o_size : pointer to storage for the number of elements in the object
 *          that were above the threshold.
 * i : current "x" location in the image.
 * j : current "y" location in the image.
 * dx : the current offset in x from point zero.
 * dy : the current offset in y from point zero.
 * xt : running sum of the intensity * dx.
 * yt : running sum of the intensity * dy.
 * t : running sum of the intensity.
 *
 * returns : nothing.
 */

void find_and_remove_object(short t_image[], int t_size_x, int t_size_y, int *o_size, int i, int j, int dx, int dy, int *xt, int *yt, int *t)
{
  short temp;

  temp = t_image[i * t_size_x + j];
  *t += temp;
  *xt += dx * temp;
  *yt += dy * temp;
  *o_size += 1;
  t_image[i * t_size_x + j] = 0;
  if (i>0){
    if (t_image[(i-1) * t_size_x + j] > 0){
      find_and_remove_object(t_image, t_size_x, t_size_y, o_size, i-1, j, dx, dy-1, xt, yt, t);
    }
  }
  if (i<(t_size_y-1)){
    if (t_image[(i+1) * t_size_x + j] > 0){
      find_and_remove_object(t_image, t_size_x, t_size_y, o_size, i+1, j, dx, dy+1, xt, yt, t);
    }
  }
  if (j>0){
    if (t_image[i * t_size_x + (j-1)] > 0){
      find_and_remove_object(t_image, t_size_x, t_size_y, o_size, i, j-1, dx-1, dy, xt, yt, t);
    }
  }
  if (j<(t_size_x-1)){
    if (t_image[i * t_size_x + (j+1)] > 0){
      find_and_remove_object(t_image, t_size_x, t_size_y, o_size, i, j+1, dx+1, dy, xt, yt, t);
    }
  }
}


/*
 * Returns the number and center of all the contiguous objects above threshold in the image.
 *
 * image[] : array of short integers representing an image.
 * size_x : the size of the x dimension of the image.
 * size_y : the size of the y dimension of the image.
 * cell_size : the size of a single cell in which to compute the stats, size should be a
 *             multiple of cell_size.
 * threshold : number of sigma above background to be a point in an object.
 * x[] : array for storage of the object x locations.
 * y[] : array for storage of the object y locations.
 * counts : (in) size of x,y (out) number of objects found.
 *
 * returns : nothing.
 */

void number_and_loc_objects(short image[], int size_x, int size_y, int cell_size, float threshold, float x[], float y[], int *counts)
{
  short *t_image;
  int i, j, t1, n, o_size, xt, yt, t;

  t_image = (short *)malloc(sizeof(short) * size_x * size_y);
  threshold_image(image, t_image, size_x, size_y, cell_size, threshold);
  for(i=0;i<*counts;i++){
    x[i] = 0.0;
    y[i] = 0.0;
  }
  n = 0;
  for(i=0;i<size_y;i++){
    t1 = i * size_x;
    for(j=0;j<size_x;j++){
      if (t_image[t1 + j] > 0){
	o_size = 0;
	xt = 0;
	yt = 0;
	t = 0;
	find_and_remove_object(t_image, size_x, size_y, &o_size, i, j, 0, 0, &xt, &yt, &t);
	if((o_size > 2) && (n < *counts) && (t > 0)){
	  x[n] = ((float)j) + ((float)xt)/((float)t);
	  y[n] = ((float)i) + ((float)yt)/((float)t);
	  n++;
	}
      }
    }
  }
  free(t_image);
  *counts = n;
}


/*
 * The MIT License
 *
 * Copyright (c) 2009 Zhuang Lab, Harvard University
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 */
