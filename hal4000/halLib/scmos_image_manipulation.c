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
 * gcc -c scmos_image_manipulation.c -O3
 * gcc -shared -o scmos_image_manipulation.dll scmos_image_manipulation.o
 *
 * Compilation (linux):
 * gcc -fPIC -g -c -Wall scmos_image_manipulation.c -O3
 * gcc -shared -Wl,-soname,scmos_image_manipulation.so.1 -o scmos_image_manipulation.so.1.0.1 scmos_image_manipulation.o -lc 
 * ln -s scmos_image_manipulation.so.1.0.1 scmos_image_manipulation.so
 *
 */

#include <stdlib.h>
#include <stdio.h>

/* function definitions */
void rescaleImage000(unsigned char*, unsigned short *, int, int, int, int, int *, int *);

/* functions */

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
 * @param image_min The minimum value in image.
 * @param image_max The maxiumum value in image.
 */
void rescaleImage000(unsigned char * scaled_image, unsigned short *image, int image_width, int image_height, int display_min, int display_max, int *image_min, int *image_max)
{
  int cur_min,cur_max,i,image_size;
  double min,scale,temp;

  min = (double)display_min;
  scale = 255.0/((double)(display_max - display_min));

  image_size = image_width * image_height;
  cur_min = image[0];
  cur_max = image[0];
  for(i=0;i<image_size;i++){

    if(image[i]<cur_min){
      cur_min = image[i];
    }
    if(image[i]>cur_max){
      cur_max = image[i];
    }

    temp = (double)image[i] - min;
    temp = temp*scale;
    if(temp < 0.0){
      temp = 0.0;
    }
    if(temp > 255.0){
      temp = 255.0;
    }
    scaled_image[i] = (unsigned char)(temp + 0.5);
  }

  *image_min = cur_min;
  *image_max = cur_max;
}

/* Transpose */
void rescaleImage001(unsigned char * scaled_image, unsigned short *image, int image_width, int image_height, int display_min, int display_max, int *image_min, int *image_max)
{
  int cur_min,cur_max,i,j,ij;
  double min,scale,temp;

  min = (double)display_min;
  scale = 255.0/((double)(display_max - display_min));

  printf("%d %d\n", image_width, image_height);

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

      temp = (double)image[ij] - min;
      temp = temp*scale;
      if(temp < 0.0){
	temp = 0.0;
      }
      else if(temp > 255.0){
	temp = 255.0;
      }
      scaled_image[j*image_width+i] = (unsigned char)(temp + 0.5);
    }
  }

  *image_min = cur_min;
  *image_max = cur_max;
}

/* Flip Vertical */
void rescaleImage010(unsigned char * scaled_image, unsigned short *image, int image_width, int image_height, int display_min, int display_max, int *image_min, int *image_max)
{
  int cur_min,cur_max,i,j,ij;
  double min,scale,temp;

  min = (double)display_min;
  scale = 255.0/((double)(display_max - display_min));

  printf("%d %d\n", image_width, image_height);

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

      temp = (double)image[ij] - min;
      temp = temp*scale;
      if(temp < 0.0){
	temp = 0.0;
      }
      else if(temp > 255.0){
	temp = 255.0;
      }
      scaled_image[i*image_height+(image_height-j-1)] = (unsigned char)(temp + 0.5);
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
