/*
 * @file
 *
 * A C shim library to assist in interfacing to Spinnaker with 
 * Python. This primarily handles spinImageEvent callbacks
 * which enable us to take continuous movies instead of grabbing
 * a series of random images.
 *
 * Compile using scons and storm-control/SConstruct.
 *
 * $ cd storm-control
 * $ path/to/scons.bat 
 *
 * Hazen 03/18
 *
 *
 * Compilation (windows / MinGW):
 *
 * c:\MinGW\bin\gcc.exe -c spinshim.c -I"C:\Program Files\Point Grey Research\Spinnaker\include\spinc" -I"C:\MinGW\x86_64-w64-mingw32\include"
 * c:\MinGW\bin\gcc.exe -shared -o spinshim.dll spinshim.o -L"C:\Program Files\Point Grey Research\Spinnaker\bin64\vs2013" -lSpinnakerC_v120
 *
 * Then copy the dll to storm-control/storm_control/c_libraries
 */

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#include "SpinnakerC.h"


typedef enum _spinShimError{

  SPINSHIM_ERR_SUCCESS = 0,
  
  SPINSHIM_ERR_ERROR = -2001,
  SPINSHIM_ERR_BUFFER_OVERFLOW = -2002,
  SPINSHIM_ERR_INCORRECTFORMAT = -2003,
  SPINSHIM_ERR_INCORRECTSIZE = -2004,
  SPINSHIM_ERR_NO_NEW_IMAGES = -2005,
  SPINSHIM_ERR_UNKNOWNFORMAT = -2006,
 
} spinShimError;


typedef struct {
  int pixel_format;  /* Image pixel format. */
  
  size_t height;     /* Image height in pixels. */
  size_t im_size;    /* Image size in bytes. */
  size_t width;      /* Image width in pixels. */
  
  void *data;        /* The raw image data. */
} image;

  
typedef struct {
  int b_len;               /* Number of images in the buffer. */
  int cam_index;           /* Index of the most recent image from the camera. */
  int err_code;            /* Current error code. */
  int read_index;          /* Index of the last image read out of buffer. */

  unsigned int n_images;   /* Total number of images captured. */
  
  spinImageEvent im_event; /* Image event.. */
  
  image *images;           /* Array of pointers which will point to the retrieved images. */  
} imageEvent;


int configureImageEvent(spinCamera, imageEvent **, int);
int getNextImage(imageEvent *, image *);
void onImageEvent(spinImage, void *);
int releaseImageEvent(spinCamera, imageEvent *);

/*
 * Configure image event handling.
 */
int configureImageEvent(spinCamera hcam, imageEvent **ie, int buffer_len)
{
  int i;
  spinError err;

  *ie = (imageEvent *)malloc(sizeof(imageEvent));
  
  (*ie)->b_len = buffer_len;
  (*ie)->cam_index = -1;
  (*ie)->err_code = SPINSHIM_ERR_SUCCESS;
  (*ie)->n_images = 0;
  (*ie)->read_index = 0;

  (*ie)->images = (image *)malloc(sizeof(image) * buffer_len);
  for (i=0;i<buffer_len;i++){
    (*ie)->images[i].data = NULL;
  }

  /* Create event handler and register with Spinnaker. */
  err = spinImageEventCreate(&((*ie)->im_event), onImageEvent, (void*)(*ie));
  if (err != SPINNAKER_ERR_SUCCESS){
    printf("spinshim: Unable to create event. Aborting with Spinnaker error %d.\n", err);
    return err;
  }
  err = spinCameraRegisterImageEvent(hcam, (*ie)->im_event);
  if (err != SPINNAKER_ERR_SUCCESS){
    printf("spinshim: Unable to register event. Aborting with Spinnaker error %d.\n", err);
    return err;
  }

  return SPINSHIM_ERR_SUCCESS;
}


/*
 * Call this repeatedly until it returns SPINSHIM_ERR_NO_NEW_IMAGES 
 * to get all of the images from the buffer.
 *
 * This will return an image structure. The memory that ie_im->data 
 * points to is controlled by the Spinnaker library, so it is a bad
 * idea to free it. The ie_im->data pointer is set to NULL as an
 * indicator that the data has been copied.
 */
int getNextImage(imageEvent *ie, image *im)
{
  int i,j;
  uint16_t pval;
  uint8_t *data8;
  uint16_t *data16, *hal_image;
  image* ie_im;

  /* Return if there are no new images. */
  if (ie->cam_index == -1){
    return SPINSHIM_ERR_NO_NEW_IMAGES;
  }
  if (ie->read_index == ie->cam_index){
    return SPINSHIM_ERR_NO_NEW_IMAGES;
  }

  /* Return if there are errors. */
  if (ie->err_code != SPINSHIM_ERR_SUCCESS){
    return ie->err_code;
  }
  
  /* Copy values into caller provide image structure. */
  ie_im = &(ie->images[ie->read_index]);

  /* Check that the pixel format is as expected. */
  if (im->pixel_format != ie_im->pixel_format){
    printf("SpinShim: Incorrect pixel format, expected %d, got %d\n", im->pixel_format, ie_im->pixel_format);
    return SPINSHIM_ERR_INCORRECTFORMAT;
  }

  /* Check that the image size is correct. */
  if (im->height != ie_im->height){
    printf("SpinShim: Incorrect height, expected %d, got %d\n", im->height, ie_im->height);
    return SPINSHIM_ERR_INCORRECTSIZE;    
  }

  if (im->width != ie_im->width){
    printf("SpinShim: Incorrect width, expected %d, got %d\n", im->width, ie_im->width);
    return SPINSHIM_ERR_INCORRECTSIZE;
  }  

  /* 
   * Convert and image to correct format, while also copying
   * into space allocated by user.
   */
  switch (im->pixel_format){

  case PixelFormat_Mono8: // 3
  
    /* Convert Mono8 to 16 bit unsigned integer. */
    data8 = (uint8_t *)ie_im->data;
    hal_image = (uint16_t *)im->data;
    for(i=0;i<ie_im->im_size;i++){
      hal_image[i] = data8[i];
    }
    break;

  case PixelFormat_Mono12p : // 8
    /* Convert Mono12p to 16 bit unsigned integer. */    
    data8 = (uint8_t *)ie_im->data;
    hal_image = (uint16_t *)im->data;
    j = 0;
    for(i=0;i<ie_im->im_size;i+=3){
    
      /* First 12 bits */
      pval = (uint16_t)data8[i];
      pval += 256*(uint16_t)(data8[i+1] & 0x0F);
      hal_image[j] = pval;
      j += 1;
      
      /* Second 12 bits */
      pval = 16*(uint16_t)data8[i+2];
      pval += (uint16_t)((data8[i+1] & 0xF0) >> 4);
      hal_image[j] = pval;
      j += 1;
    }
    break;

  case PixelFormat_Mono16: // 10
    /* 
     * Convert Mono16 to 16 bit unsigned integer.
     *
     * FIXME: Designed specifically for 12 bit cameras.
     */
    data16 = (uint16_t *)ie_im->data;
    hal_image = (uint16_t *)im->data;
    for(i=0;i<ie_im->im_size/2;i++){
      hal_image[i] = data16[i] >> 4;
    }
    break;

  case PixelFormat_Mono12Packed : // 214
    /* Convert Mono12Packed to 16 bit unsigned integer. */    
    data8 = (uint8_t *)ie_im->data;
    hal_image = (uint16_t *)im->data;
    j = 0;
    for(i=0;i<ie_im->im_size;i+=3){
    
      /* First 12 bits */
      pval = 16 * ((uint16_t)data8[i]);
      pval += (uint16_t)(data8[i+1] & 0x0F);
      hal_image[j] = pval;
      j += 1;
      
      /* Second 12 bits */
      pval = 16 * ((uint16_t)data8[i+2]);
      pval += (uint16_t)((data8[i+1] & 0xF0) >> 4);	    
      hal_image[j] = pval;
      j += 1;
    }
    break;

  default :
    printf("SpinShim: Unknown pixel format %d\n", im->pixel_format);
    return SPINSHIM_ERR_UNKNOWNFORMAT;
  }

  /* Set data to NULL as a mark that this image has been transferred out. */
  ie_im->data = NULL;

  /* Increment read index. */
  ie->read_index += 1;
  if (ie->read_index >= ie->b_len){
    ie->read_index = 0;
  }  

  return ie->err_code;
}


/*
 * This is the callback that will get called every time there is a new image.
 */
void onImageEvent(spinImage h_image, void *user_data)
{
  bool8_t is_incomplete;
  int im_index;
  size_t height, im_size, width;
  spinError err;
  spinImageStatus im_status;
  spinPixelFormatEnums pixel_format;

  image *im;
  imageEvent *ie;
  void *data;

  ie = (imageEvent *)user_data;
  im_index = ie->cam_index + 1;
  if (im_index >= ie->b_len){
    im_index = 0;
  }
  im = &(ie->images[im_index]);

  /* Check for buffer overflow. */
  if (im->data != NULL){
    printf("spinshim: Buffer overflow detected.\n");
    ie->err_code = SPINSHIM_ERR_BUFFER_OVERFLOW;
    return;
  }
  
  /* Check that image is complete. */
  err = spinImageIsIncomplete(h_image, &is_incomplete);
  if (err != SPINNAKER_ERR_SUCCESS){
    printf("spinshim: Unable to determine image completion. Error code %d.\n", err);
    return;      
  }

  /* Report why the image is incomplete. */
  if (is_incomplete){
    err = spinImageGetStatus(h_image, &im_status);
    if (err != SPINNAKER_ERR_SUCCESS){
      printf("spinshim: Unable to retrieve image status. Error code %d.\n", err);
    }
    else {
      printf("spinshim: Image incomplete with image status %d.\n", im_status);
    }
    return;
  }

  /* Get image dimensions, format, size in bytes. */
  height = 0;
  err = spinImageGetHeight(h_image, &height);
  if (err != SPINNAKER_ERR_SUCCESS){
    printf("spinshim: Unable to retrieve image height. Error code %d.\n", err);
  }
  im->height = height;

  im_size = 0;
  err = spinImageGetSize(h_image, &im_size);
  if (err != SPINNAKER_ERR_SUCCESS){
    printf("spinshim: Unable to retrieve image size. Error code %d.\n", err);
  }
  im->im_size = im_size;
  
  width = 0;
  err = spinImageGetWidth(h_image, &width);
  if (err != SPINNAKER_ERR_SUCCESS){
    printf("spinshim: Unable to retrieve image width. Error code %d.\n", err);
  }
  im->width = width;

  pixel_format = 0;
  err = spinImageGetPixelFormat(h_image, &pixel_format);
  if (err != SPINNAKER_ERR_SUCCESS){
    printf("spinshim: Unable to retrieve image pixel format. Error code %d.\n", err);
  }
  im->pixel_format = (int)pixel_format;

  /* 
   * Get image data. It appears that Spinnaker is returning a pointers to
   * memory that it pre-allocated, e.g. "StreamDefaultBufferCount" and that
   * it is re-cycling.
   *
   * So:
   * (1) Don't try and free the memory that spinImageGetData() returns or 
   *     you will get an access violation.
   * (2) StreamDefaultBufferCount should be >= the number of buffers in
   *     the imageEvent structure.
   */
  err = spinImageGetData(h_image, &data);
  if (err != SPINNAKER_ERR_SUCCESS){
    printf("spinshim: Unable to retrieve image data. Error code %d.\n", err);
  }
  im->data = data;

  /*
  printf("Got image %d x %d (%d bytes), number %d, index %d\n", (int)im->width, (int)im->height, (int)im->im_size, (int)ie->n_images, (int)ie->cam_index);
  */

  /* Update current image. */
  ie->n_images += 1;
  ie->cam_index = im_index;
}


/*
 * Call this when finished with image event handling.
 */
int releaseImageEvent(spinCamera hcam, imageEvent *ie)
{
  int i;
  spinError err;

  image *im;

  /* 
   * Free image storage. Don't free the data elements of the images as that
   * memory is managed by Spinnaker.
   */     
  free(ie->images);

  /* Deregister and destroy image event. */
  err = spinCameraUnregisterImageEvent(hcam, ie->im_event);
  if (err != SPINNAKER_ERR_SUCCESS){
    printf("spinshim: Unable to unregister event. Aborting with Spinnaker error %d.\n", err);
    return err;
  }

  err = spinImageEventDestroy(ie->im_event);
  if (err != SPINNAKER_ERR_SUCCESS){
    printf("spinshim: Unable to destroy event. Aborting with Spinnaker error %d.\n", err);
    return err;
  }
  
  free(ie);
    
  return SPINSHIM_ERR_SUCCESS;
}

/*
 * The MIT License
 *
 * Copyright (c) 2016 Zhuang Lab, Harvard University
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
