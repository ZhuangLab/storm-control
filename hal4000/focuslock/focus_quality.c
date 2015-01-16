/*
 * @file
 *
 * Methods for calculating how well focused and image is.
 *
 * Hazen 8/10
 *
 * compilation:
 * gcc -c focus_quality.c
 * gcc -shared -o focus_quality.dll focus_quality.o
 *
 */

#include <stdlib.h>

/* function definitions */

float imageGradient(short *, int, int);


/* functions */

/* 
 * imageGradient
 *
 * Compute the sum of the pixel by pixel difference along the "X" axis.
 * Normalize this value by the overall sum of the image. 
 */

float imageGradient(short *image, int image_x, int image_y){
  int i, j, temp_i;
  int diff, sum;

  sum = 0;
  diff = 0;
  for(i=0;i<image_y;i++){
    temp_i = i * image_x;
    for(j=0;j<(image_x-1);j++){
      diff += abs(image[temp_i + j + 1] - image[temp_i + j]);
      sum += image[temp_i + j];
    }
  }
  return ((float)diff/(float)sum);
}

/*
 * The MIT License
 *
 * Copyright (c) 2010 Zhuang Lab, Harvard University
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
