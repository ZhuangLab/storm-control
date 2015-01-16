/*
 * @file
 *
 * Object finding code that find peaks by identifying local maxima, 
 * checking if they have a peak like shape, then computing the
 * first moment to determine the peak center.
 * 
 * Hazen 09/13
 * 
 * Windows:
 *  gcc -c LMMoment.c
 *  gcc -shared -o LMMoment.dll LMMoment.o
 */

/* Include */

#include <stdlib.h>
#include <stdio.h>
#include <math.h>

/*
 * Peak definition.
 *
 * BSIZE should be half of peak dimension in x/y.
 * 1 in the peak definition means boundary.
 * 2 in the peak definition means center.
 * peak x/y dimensions should be odd.
 */

#define BSIZE 5

static int bdy_len;
static int cnt_len;

static int peak[81] = {0, 0, 0, 1, 1, 1, 0, 0, 0,
		       0, 0, 1, 2, 2, 2, 1, 0, 0,
		       0, 1, 2, 2, 2, 2, 2, 1, 0,
		       1, 2, 2, 2, 2, 2, 2, 2, 1,
		       1, 2, 2, 2, 2, 2, 2, 2, 1,
		       1, 2, 2, 2, 2, 2, 2, 2, 1,
		       0, 1, 2, 2, 2, 2, 2, 1, 0,
		       0, 0, 1, 2, 2, 2, 1, 0, 0,
		       0, 0, 0, 1, 1, 1, 0, 0, 0};

static int *bdy_dx;
static int *bdy_dy;
static int *cnt_dx;
static int *cnt_dy;


/*
 * Function Declarations.
 */

void cleanup(void);
void initialize(void);
int isLocalMaxima(short [], int, int, int, int);
int isPeak(short [], int, int, int, int, int);
void numberAndLocObjects(short [], int, int, int, float [], float [], int *);
void peakPosition(short [], int, int, int, int, int, float *, float *);


/* 
 * Functions.
 */

/*
 * cleanup()
 */
void cleanup(void)
{
  free(bdy_dx);
  free(bdy_dy);
  free(cnt_dx);
  free(cnt_dy);
}

/*
 * initialize()
 */
void initialize(void)
{
  int i,j,k,l;
  int size;

  size = 2*BSIZE-1;

  bdy_len = 0;
  cnt_len = 0;
  for (i=0;i<size*size;i++){
    if (peak[i]==1){
      bdy_len++;
    }
    else if (peak[i]==2){
      cnt_len++;
    }
  }

  bdy_dx = (int *)malloc(sizeof(int)*bdy_len);
  bdy_dy = (int *)malloc(sizeof(int)*bdy_len);

  cnt_dx = (int *)malloc(sizeof(int)*cnt_len);
  cnt_dy = (int *)malloc(sizeof(int)*cnt_len);

  k = l = 0;
  for (i=0;i<size;i++){
    for (j=0;j<size;j++){
      if (peak[i*size+j] == 1){
	bdy_dy[k] = i - BSIZE + 1;
	bdy_dx[k] = j - BSIZE + 1;
	k++;
      }
      else if (peak[i*size+j] == 2){
	cnt_dx[l] = i - BSIZE + 1;
	cnt_dy[l] = j - BSIZE + 1;
	// printf(" %d %d\n", cnt_dx[l], cnt_dy[l]);
	l++;
      }
    }
  }
}

/*
 * isLocalMaxima()
 *
 * image[] : array of short integers representing an image.
 * size_x : the size of the x dimension of the image.
 * size_y : the size of the y dimension of the image.
 * x : x position of pixel of interest.
 * y : y position of pixel of interest.
 *
 * returns 1 if this is a local maxima, zero otherwise.
 */
int isLocalMaxima(short image[], int size_x, int size_y, int x, int y)
{
  int cur;

  cur = x*size_y + y;
  if(image[cur] <= image[cur - size_y - 1]){
    return 0;
  }
  if(image[cur] <= image[cur - size_y]){
    return 0;
  }
  if(image[cur] <= image[cur - size_y + 1]){
    return 0;
  }
  if(image[cur] <= image[cur - 1]){
    return 0;
  }
  if(image[cur] < image[cur + 1]){
    return 0;
  }
  if(image[cur] <= image[cur + size_y - 1]){
    return 0;
  }
  if(image[cur] < image[cur + size_y]){
    return 0;
  }
  if(image[cur] < image[cur + size_y + 1]){
    return 0;
  }

  return 1;
}

/*
 * isPeak()
 *
 * image[] : array of short integers representing an image.
 * size_x : the size of the x dimension of the image.
 * size_y : the size of the y dimension of the image.
 * x : x position of pixel of interest.
 * y : y position of pixel of interest.
 * threshold : peak height above background ring to be considered a peak.
 *
 * returns the mean on the boundary if this is a peak, zero otherwise.
 *   This is assuming that there is always at least some offset.
 *
 */
int isPeak(short image[], int size_x, int size_y, int x, int y, int threshold)
{
  int i,cur,mean,sum,tmp;

  cur = image[x*size_y+y];
  sum = 0;
  for(i=0;i<bdy_len;i++){
    tmp = image[(x + bdy_dx[i])*size_y + (y + bdy_dy[i])];
    if (cur < (tmp + threshold)){
      return 0;
    }
    sum += tmp;
  }

  mean = sum/bdy_len;

  return mean;
}

/*
 * numberAndLocObjects()
 *
 * Returns the number and center of all the contiguous objects above threshold in the image.
 *
 * image[] : array of short integers representing an image.
 * size_x : the size of the x dimension of the image.
 * size_y : the size of the y dimension of the image.
 * threshold : peak height above background ring to be considered a peak.
 * x[] : array for storage of the object x locations.
 * y[] : array for storage of the object y locations.
 * counts : (in) size of x,y (out) number of objects found.
 *
 * returns nothing.
 */
void numberAndLocObjects(short image[], int size_x, int size_y, int threshold, float x_arr[], float y_arr[], int *counts)
{
  int n,x,y;
  int mean;

  n = 0;
  for(x=BSIZE;x<(size_x-BSIZE);x++){
    for(y=BSIZE;y<(size_y-BSIZE);y++){
      if(isLocalMaxima(image, size_x, size_y, x, y)){
	mean = isPeak(image, size_x, size_y, x, y, threshold);
	if(mean > 0){
	  peakPosition(image, size_x, size_y, x, y, mean, &(x_arr[n]), &(y_arr[n]));
	  n++;
	  if(n == *counts){
	    x = size_x;
	    y = size_y;
	  }
	}
      }
    }
  }

  *counts = n;
}

/*
 * peakPosition()
 *
 * Returns the center position of the peak as calculated
 * from the first moment of the peak.
 *
 * image[] : array of short integers representing an image.
 * size_x : the size of the x dimension of the image.
 * size_y : the size of the y dimension of the image.
 * x : x position of pixel of interest.
 * y : y position of pixel of interest.
 * mean : mean intensity on the boundary.
 * px : peak position in x.
 * py : peak position in y.
 *
 * returns nothing.
 */
void peakPosition(short image[], int size_x, int size_y, int x, int y, int mean, float *px, float *py)
{
  int cur,i,sum,sumx,sumy;

  sum = sumx = sumy = 0;
  for(i=0;i<cnt_len;i++){
    cur = image[(x + cnt_dx[i])*size_y + (y + cnt_dy[i])] - mean;
    sum += cur;
    sumx += cur*cnt_dx[i];
    sumy += cur*cnt_dy[i];
  }

  if (sum > 0){
    *px = ((float)y) + ((float)sumy)/((float)sum);
    *py = ((float)x) + ((float)sumx)/((float)sum);
  }
  else{
    *px = -1.0;
    *py = -1.0;
  }

}

/*
 * The MIT License
 *
 * Copyright (c) 2013 Zhuang Lab, Harvard University
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
