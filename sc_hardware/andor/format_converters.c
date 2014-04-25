/*
 * @file
 *
 * Convert Andor camera data into various other formats. At
 * present most of this is not used anymore.
 *
 * Hazen 2/09
 *
 * compilation:
 * gcc -c format_converters.c
 * gcc -shared -o format_converters.dll format_converters.o
 *
 * Note that when writing C code I am somehow forced to use
 * strangely abbreviated variable names and to make other
 * poor style choices.
 */


/* function definitions */

int andorToQtImage(unsigned char *, int, int, int, int, int *, int *);
int andorToBigEndian(unsigned char *, unsigned char *, int);


/* functions */

/* Converts to thresholded 8 bit for Qt */
/*
 * FIXME: do we still use this? I think is now done with numpy.
 */
int andorToQtImage(unsigned char *andor_data, int qt_data_ptr, int number_pixels, int min, int max, int *i_min, int *i_max){
  int i, range;
  long val;
  unsigned char *qt_image_data = (unsigned char *)qt_data_ptr;
  
  range = max - min;
  for(i=0;i<number_pixels;i++){
    val = andor_data[i*2] + andor_data[i*2+1] * 256;
    if(val < *i_min) *i_min = val;
    if(val > *i_max) *i_max = val;
    val = (val - min)*256/range;
    if(val < 0) val = 0;
    if(val > 255) val = 255;
    qt_image_data[i] = (char)val;
  }
}

/* Converts to big endian, for historical reasons related 
   to a poor decision by the designers of LabView. */

int andorToBigEndian(unsigned char *andor_data, unsigned char *be_data, int bytes){
  int i;

  for(i=0;i<bytes;i+=2){
    be_data[i] = andor_data[i+1];
    be_data[i+1] = andor_data[i];
  }
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
