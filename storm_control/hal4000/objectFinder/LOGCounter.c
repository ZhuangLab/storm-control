/*
 * @file
 *
 * Laplacian of Gaussian based object finder.
 *
 * Hazen 3/09
 *
 * Linux:
 *  gcc -fPIC -g -c -Wall LOGCounter.c
 *  gcc -shared -Wl,-soname,LOGCounter.so.1 -o LOGCounter.so.1.0.1 LOGCounter.o -lc
 *
 * Windows:
 *  gcc -c LOGCounter.c
 *  gcc -shared -o LOGCounter.dll LOGCounter.o
 *
 */


/* Includes */
#include <stdlib.h>
#include <stdio.h>
#include <math.h>


/* Declarations */
int kernelSize(float);
void createKernel(int*, float);
int countObjects(short*, int*, int, int, int, int, int);


/* Functions */

/*
 * Return the kernel.
 *
 * spot_size: the expected size (sigma) of a single spot.
 */
int kernelSize(float spot_size)
{
  int temp;

  temp = ((int)(spot_size * 6.0));
  if((temp % 2) == 0) temp++;
  return(temp);
}

/* 
 * Create the kernel.
 *
 * kernel : space allocated for kernel storage, this should be
 *          able to store kernelSize() x kernelSize() integers. 
 * spot_size: the expected size (sigma) of a single spot.
 *
 * LOG function reference:
 *   http://academic.mu.edu/phys/matthysd/web226/Lab02.htm
 */
void createKernel(int *kernel, float spot_size)
{
  short i,j;
  int kernel_size, half_ks;
  float x,y,val,min,sum,*f_kernel;

  kernel_size = kernelSize(spot_size);
  half_ks = (int)(0.5 * kernel_size);
  
  /* first calculate the kernel as floats */
  sum = 0.0;
  min = 0.0;
  f_kernel = (float *)malloc(sizeof(float) * kernel_size * kernel_size);
  for(i=0;i<kernel_size;i++){
    y = (float)(i - half_ks);
    for(j=0;j<kernel_size;j++){
      x = (float)(j - half_ks);
      val = -1.0/(3.14159 * spot_size * spot_size * spot_size * spot_size);
      val = val * (1.0 - (x * x + y * y)/(2.0 * spot_size * spot_size));
      val = val * exp(-1.0 * (x * x + y * y)/(2.0 * spot_size * spot_size));
      if(val < min) min = val;
      sum += val;
      f_kernel[i * kernel_size + j] = val;
    }
  }

  /* convert kernel to integers, rescaling in the process */
  sum = sum/((float)(kernel_size * kernel_size));
  for(i=0;i<(kernel_size*kernel_size);i++){
    kernel[i] = (int)((f_kernel[i] - sum) * (100.0/min));
  }

  /* cleanup */
  free(f_kernel);
}

/*
 * Count the number of objects.
 *
 * image : the image (16 bit integers).
 * kernel : the kernel from createKernel().
 * image_x : image size in x.
 * image_y : image size in y.
 * kernel_size : the size of the kernel.
 * threshold : the number above which something is an object.
 * offset : the difference between the sum of the kernel and 0.
 */
int countObjects(short *image, int *kernel, int image_x, int image_y, int kernel_size, int threshold, int offset)
{
  int i,j,k,l,ix,iy,ky;
  int half_ks, sum, counts;

  counts = 0;
  half_ks = (int)(0.5 * kernel_size);
  for (i=half_ks;i<(image_y - half_ks);i++){
    for (j=half_ks;j<(image_x - half_ks);j++){
      sum = 0;
      for (k=0;k<kernel_size;k++){
	iy = (i + k - half_ks) * image_x;
	ky = k * kernel_size;
	for (l=0;l<kernel_size;l++){
	  ix = j + l - half_ks;
	  sum += image[iy + ix] * kernel[ky + l] - offset;
	}
      }
      if(sum > threshold) counts++;
    }
  }
  return(counts);
}
