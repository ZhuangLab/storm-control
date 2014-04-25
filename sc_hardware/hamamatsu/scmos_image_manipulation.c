/*
 * @file
 *
 * Perform various manipulations on sCMOS image data. This is written
 * in C for performance reasons.
 *
 * Hazen 10/13
 *
 * compilation:
 * gcc -c scmos_image_manipulation.c -O3
 * gcc -shared -o scmos_image_manipulation.dll scmos_image_manipulation.o
 */

/* function definitions */
void rescaleImage(unsigned char*, unsigned short *, int, int, int, int *, int *);

/* functions */

/* rescaleImage
 *
 * Converts to thresholded 8 bit for Qt.
 *
 * @param scaled_image Storage for the scaled image.
 * @param image The original image data from the camera, assumed to be 16 bit.
 * @param image_size The number of pixels in the image.
 * @param display_min The value in image that will be zero in the scaled image.
 * @param display_max The value in image that will be 255 in the scaled image.
 * @param image_min The minimum value in image.
 * @param image_max The maxiumum value in image.
 */
void rescaleImage(unsigned char * scaled_image, unsigned short *image, int image_size, int display_min, int display_max, int *image_min, int *image_max)
{
  int cur_min,cur_max,i;
  double min,scale,temp;

  min = (double)display_min;
  scale = 255.0/((double)(display_max - display_min));

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
