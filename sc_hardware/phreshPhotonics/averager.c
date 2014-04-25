/*
 * @file
 *
 * C helper for PhreshQPD class to do fast averaging of an array of numbers.
 *
 * Hazen 4/09
 *
 * FIXME: This should be replaced by with numpy. In retrospect I'm not
 *   sure why I was concerned about adding external dependencies.
 *
 * Hazen 11/13
 *
 * compilation:
 * gcc -c averager.c
 * gcc -shared -o averager.dll averager.o
 */

void averager(double *data, double *results, int samples, int channels)
{
  int i,j;
  double average;
  double *cur;

  cur = data;
  for(i=0;i<channels;i++){
    average = 0.0;
    for(j=0;j<samples;j++){
      average += *cur;
      cur++;
    }
    results[i] = average/((double)samples);
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
