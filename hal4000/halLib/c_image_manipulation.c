/*
 * @file
 *
 * Perform various manipulations on sCMOS image data. This is written
 * in C for performance reasons.
 *
 * Hazen 10/13
 *
 * Add additional functions to cover all the orientation possibilities.
 *
 * Hazen 09/15
 *
 *
 * Compilation (windows):
 * gcc -c c_image_manipulation.c -O3
 * gcc -shared -o c_image_manipulation.dll c_image_manipulation.o
 *
 * Compilation (linux):
 * gcc -fPIC -g -c -Wall c_image_manipulation.c -O3
 * gcc -shared -Wl,-soname,c_image_manipulation.so.1 -o c_image_manipulation.so.1.0.1 c_image_manipulation.o -lc 
 * ln -s c_image_manipulation.so.1.0.1 c_image_manipulation.so
 *
 */

#include <stdlib.h>
#include <stdio.h>
#include <stdint.h>

/* function definitions */
int compare(uint8_t*, uint8_t*, int);
void rescaleImage000(uint8_t*, unsigned short *, int, int, int, int, int, double, int *, int *);
void rescaleImage001(uint8_t*, unsigned short *, int, int, int, int, int, double, int *, int *);
void rescaleImage010(uint8_t*, unsigned short *, int, int, int, int, int, double, int *, int *);
void rescaleImage011(uint8_t*, unsigned short *, int, int, int, int, int, double, int *, int *);
void rescaleImage100(uint8_t*, unsigned short *, int, int, int, int, int, double, int *, int *);
void rescaleImage101(uint8_t*, unsigned short *, int, int, int, int, int, double, int *, int *);
void rescaleImage110(uint8_t*, unsigned short *, int, int, int, int, int, double, int *, int *);
void rescaleImage111(uint8_t*, unsigned short *, int, int, int, int, int, double, int *, int *);

/* 
 * Functions 
 *
 * Yes there is horrible duplication here as pretty much the only difference between
 * the functions is how the indexing is done. I did not want to pass in an indexing
 * function as I'm trying to keep the optimized. Though this is probably a case of
 * premature optimization. In Lisp the problem would be solved with a macro..
 *
 */

/* compare
 *
 * Does a bytewise comparison of two numpy arrays.
 *
 * @param array1 The first array.
 * @param array2 The second array.
 *
 * @return The number of differences greater than 1.
 */
int compare(uint8_t* array1, uint8_t* array2, int n_values)
{
  int i,ndiff, v1, v2;

  ndiff = 0;
  for(i=0;i<n_values;i++){
    v1 = (int)array1[i];
    v2 = (int)array2[i];
    if (abs(v1-v2) > 0){
      ndiff += 1;
    }
  }

  return ndiff;
}

/* rescaleImage000
 *
 * Converts to thresholded 8 bit for Qt.
 *
 * @param scaled_image Storage for the scaled image.
 * @param image The original image data from the camera, assumed to be 16 bit.
 * @param image_width The width of the image (the "slow" dimension).
 * @param image_height The height of the image (the "fast" dimension).
 * @param display_min The value in image that will be zero in the scaled image.
 * @param display_max The value in image that will be 255 in the scaled image.
 * @param saturated The value at which the camera is saturated.
 * @param max_range The maximum value when rescaled.
 * @param image_min The minimum value in image.
 * @param image_max The maxiumum value in image.
 */
void rescaleImage000(uint8_t *scaled_image, unsigned short *image, int image_width, int image_height, int display_min, int display_max, int saturated, double max_range, int *image_min, int *image_max)
{
  int cur_min,cur_max,i,image_size;
  double min,scale,temp;

  min = (double)display_min;
  scale = max_range/((double)(display_max - display_min));

  image_size = image_width * image_height;
  cur_min = image[0];
  cur_max = image[0];
  for(i=0;i<image_size;i++){

    if(image[i]<cur_min){
      cur_min = image[i];
    }
    else if(image[i]>cur_max){
      cur_max = image[i];
    }

    if (image[i] >= saturated){
      scaled_image[i] = 255;
    }
    else{
      temp = (double)image[i] - min;
      temp = temp*scale;
      if(temp < 0.0){
	temp = 0.0;
      }
      else if(temp > max_range){
	temp = max_range;
      }
      scaled_image[i] = (uint8_t)(temp + 0.5);
    }
  }

  *image_min = cur_min;
  *image_max = cur_max;
}

/* Transpose */
void rescaleImage001(uint8_t *scaled_image, unsigned short *image, int image_width, int image_height, int display_min, int display_max, int saturated, double max_range, int *image_min, int *image_max)
{
  int cur_min,cur_max,i,ij,j;
  double min,scale,temp;

  min = (double)display_min;
  scale = max_range/((double)(display_max - display_min));

  cur_min = image[0];
  cur_max = image[0];
  for(i=0;i<image_width;i++){
    for(j=0;j<image_height;j++){

      ij = i*image_height + j;
      
      if(image[ij]<cur_min){
	cur_min = image[ij];
      }
      else if(image[ij]>cur_max){
	cur_max = image[ij];
      }
      
      if (image[ij] >= saturated){
	scaled_image[j*image_width+i] = 255;
      }
      else{
	temp = (double)image[ij] - min;
	temp = temp*scale;
	if(temp < 0.0){
	  temp = 0.0;
	}
	else if(temp > max_range){
	  temp = max_range;
	}
	scaled_image[j*image_width+i] = (uint8_t)(temp + 0.5);
      }
    }
  }

  *image_min = cur_min;
  *image_max = cur_max;
}

/* Flip vertical */
void rescaleImage010(uint8_t *scaled_image, unsigned short *image, int image_width, int image_height, int display_min, int display_max, int saturated, double max_range, int *image_min, int *image_max)
{
  int cur_min,cur_max,i,ij,j;
  double min,scale,temp;

  min = (double)display_min;
  scale = max_range/((double)(display_max - display_min));

  cur_min = image[0];
  cur_max = image[0];
  for(i=0;i<image_width;i++){
    for(j=0;j<image_height;j++){

      ij = i*image_height + j;
      
      if(image[ij]<cur_min){
	cur_min = image[ij];
      }
      else if(image[ij]>cur_max){
	cur_max = image[ij];
      }
      
      if (image[ij] >= saturated){
	scaled_image[(image_width-i-1)*image_height+j] = 255;
      }
      else{
	temp = (double)image[ij] - min;
	temp = temp*scale;
	if(temp < 0.0){
	  temp = 0.0;
	}
	else if(temp > max_range){
	  temp = max_range;
	}
	scaled_image[(image_width-i-1)*image_height+j] = (uint8_t)(temp + 0.5);
      }
    }
  }

  *image_min = cur_min;
  *image_max = cur_max;
}

/* Flip vertical, then transpose */
void rescaleImage011(uint8_t *scaled_image, unsigned short *image, int image_width, int image_height, int display_min, int display_max, int saturated, double max_range, int *image_min, int *image_max)
{
  int cur_min,cur_max,i,ij,j;
  double min,scale,temp;

  min = (double)display_min;
  scale = max_range/((double)(display_max - display_min));

  cur_min = image[0];
  cur_max = image[0];
  for(i=0;i<image_width;i++){
    for(j=0;j<image_height;j++){

      ij = i*image_height + j;
      
      if(image[ij]<cur_min){
	cur_min = image[ij];
      }
      else if(image[ij]>cur_max){
	cur_max = image[ij];
      }
      
      if (image[ij] >= saturated){
	scaled_image[j*image_width+(image_width-i-1)] = 255;
      }
      else{
	temp = (double)image[ij] - min;
	temp = temp*scale;
	if(temp < 0.0){
	  temp = 0.0;
	}
	else if(temp > max_range){
	  temp = max_range;
	}
	scaled_image[j*image_width+(image_width-i-1)] = (uint8_t)(temp + 0.5);
      }
    }
  }

  *image_min = cur_min;
  *image_max = cur_max;
}

/* Flip horizontal */
void rescaleImage100(uint8_t *scaled_image, unsigned short *image, int image_width, int image_height, int display_min, int display_max, int saturated, double max_range, int *image_min, int *image_max)
{
  int cur_min,cur_max,i,ij,j;
  double min,scale,temp;

  min = (double)display_min;
  scale = max_range/((double)(display_max - display_min));

  cur_min = image[0];
  cur_max = image[0];
  for(i=0;i<image_width;i++){
    for(j=0;j<image_height;j++){

      ij = i*image_height + j;
      
      if(image[ij]<cur_min){
	cur_min = image[ij];
      }
      else if(image[ij]>cur_max){
	cur_max = image[ij];
      }
      
      if (image[ij] >= saturated){
	scaled_image[i*image_height+(image_height-j-1)] = 255;
      }
      else{
	temp = (double)image[ij] - min;
	temp = temp*scale;
	if(temp < 0.0){
	  temp = 0.0;
	}
	else if(temp > max_range){
	  temp = max_range;
	}
	scaled_image[i*image_height+(image_height-j-1)] = (uint8_t)(temp + 0.5);
      }
    }
  }

  *image_min = cur_min;
  *image_max = cur_max;
}

/* Flip horizontal, then transpose */
void rescaleImage101(uint8_t *scaled_image, unsigned short *image, int image_width, int image_height, int display_min, int display_max, int saturated, double max_range, int *image_min, int *image_max)
{
  int cur_min,cur_max,i,ij,j;
  double min,scale,temp;

  min = (double)display_min;
  scale = max_range/((double)(display_max - display_min));

  cur_min = image[0];
  cur_max = image[0];
  for(i=0;i<image_width;i++){
    for(j=0;j<image_height;j++){

      ij = i*image_height + j;
      
      if(image[ij]<cur_min){
	cur_min = image[ij];
      }
      else if(image[ij]>cur_max){
	cur_max = image[ij];
      }
      
      if (image[ij] >= saturated){
	scaled_image[(image_height-j-1)*image_width+i] = 255;
      }
      else{
	temp = (double)image[ij] - min;
	temp = temp*scale;
	if(temp < 0.0){
	  temp = 0.0;
	}
	else if(temp > max_range){
	  temp = max_range;
	}
	scaled_image[(image_height-j-1)*image_width+i] = (uint8_t)(temp + 0.5);
      }
    }
  }

  *image_min = cur_min;
  *image_max = cur_max;
}

/* Flip horizontal, then vertical */
void rescaleImage110(uint8_t *scaled_image, unsigned short *image, int image_width, int image_height, int display_min, int display_max, int saturated, double max_range, int *image_min, int *image_max)
{
  int cur_min,cur_max,i,ij,j;
  double min,scale,temp;

  min = (double)display_min;
  scale = max_range/((double)(display_max - display_min));

  cur_min = image[0];
  cur_max = image[0];
  for(i=0;i<image_width;i++){
    for(j=0;j<image_height;j++){

      ij = i*image_height + j;
      
      if(image[ij]<cur_min){
	cur_min = image[ij];
      }
      else if(image[ij]>cur_max){
	cur_max = image[ij];
      }
      
      if (image[ij] >= saturated){
	scaled_image[(image_width-i-1)*image_height+(image_height-j-1)] = 255;
      }
      else{
	temp = (double)image[ij] - min;
	temp = temp*scale;
	if(temp < 0.0){
	  temp = 0.0;
	}
	else if(temp > max_range){
	  temp = max_range;
	}
	scaled_image[(image_width-i-1)*image_height+(image_height-j-1)] = (uint8_t)(temp + 0.5);
      }
    }
  }

  *image_min = cur_min;
  *image_max = cur_max;
}

/* Flip horizontal, then vertical, then tranpose */
void rescaleImage111(uint8_t *scaled_image, unsigned short *image, int image_width, int image_height, int display_min, int display_max, int saturated, double max_range, int *image_min, int *image_max)
{
  int cur_min,cur_max,i,ij,j;
  double min,scale,temp;

  min = (double)display_min;
  scale = max_range/((double)(display_max - display_min));

  cur_min = image[0];
  cur_max = image[0];
  for(i=0;i<image_width;i++){
    for(j=0;j<image_height;j++){

      ij = i*image_height + j;
      
      if(image[ij]<cur_min){
	cur_min = image[ij];
      }
      else if(image[ij]>cur_max){
	cur_max = image[ij];
      }
      
      if (image[ij] >= saturated){
	scaled_image[(image_height-j-1)*image_width+(image_width-i-1)] = 255;
      }
      else{
	temp = (double)image[ij] - min;
	temp = temp*scale;
	if(temp < 0.0){
	  temp = 0.0;
	}
	else if(temp > max_range){
	  temp = max_range;
	}
	scaled_image[(image_height-j-1)*image_width+(image_width-i-1)] = (uint8_t)(temp + 0.5);
      }
    }
  }

  *image_min = cur_min;
  *image_max = cur_max;
}

/*
 * The MIT License
 *
 * Copyright (c) 2015 Zhuang Lab, Harvard University
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
