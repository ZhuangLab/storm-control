/*
 * C library for the autofocus lock. 
 *
 * So named because this lock works on the same principle as 
 * the autofocus system in a SLR camera. The primary difference 
 * is the use of an IR laser to create the object to focus on.
 *
 * Hazen 9/19
 */

/* Include */
#include <stdlib.h>
#include <stdio.h>
#include <math.h>

#include <fftw3.h>

/* Structures & Types */
typedef struct afLockData {
  int downsample;
  int fft_size;
  int xo;
  int x_size;
  int yo;
  int y_size;

  double cost;
  double cost_dx;
  double cost_dy;
  double dx;
  double dy;
  double mag;
  
  double *fft_vector;
  double *im1;
  double *w1;
  double *x_freq;
  double *y_freq;
  
  fftw_plan fft_backward;
  fftw_plan fft_forward;

  fftw_complex *fft_vector_fft;
  fftw_complex *im2_fft;
  fftw_complex *xy_shift;
} afLockData;


void aflCalcShift(afLockData *);
void aflCleanup(afLockData *);
void aflCost(afLockData *);
void aflCostGradient(afLockData *);
void aflGetCost(afLockData *, double *);
void aflGetCostGradient(afLockData *, double *);
void aflGetMag(afLockData *, double *);
void aflGetOffset(afLockData *, double *);
void aflGetVector(afLockData *, double *, int);
afLockData *aflInitialize(int, int, int);
void aflNewImage(afLockData *, double *, double *, double, double);
void aflRebin(afLockData *, double *, double);


/*
 * aflCalcShift()
 *
 * Calculate shift vector at current offset estimate.
 * 
 * afld - pointer to a afLockData structure.
 */
void aflCalcShift(afLockData *afld)
{
}


/*
 * aflCleanup()
 *
 * Clean up auto focus lock fitter.
 * 
 * afld - pointer to a afLockData structure.
 */
void aflCleanup(afLockData *afld)
{
  free(afld->im1);
  free(afld->w1);
  free(afld->x_freq);
  free(afld->y_freq);

  fftw_free(afld->fft_vector);
  fftw_free(afld->fft_vector_fft);
  fftw_free(afld->im2_fft);
  fftw_free(afld->xy_shift);
  
  fftw_destroy_plan(afld->fft_forward);
  fftw_destroy_plan(afld->fft_backward);
  
  free(afld);
}


/*
 * aflCost()
 *
 * Calculate cost.
 *
 * afld - pointer to a afLockData structure.
 */
void aflCost(afLockData *afld)
{
}


/*
 * aflCostGradient()
 *
 * Calculate gradient of cost.
 *
 * afld - pointer to a afLockData structure.
 */
void aflCostGradient(afLockData *afld)
{
}


/*
 * aflGetCost()
 *
 * Returns the cost at the current estimate of the offset.
 *
 * afld - pointer afLockData structure.
 * cost - pre-allocated storage for a single element.
 */
void aflGetCost(afLockData *afld, double *cost)
{
}


/*
 * aflGetCostGradient()
 *
 * Returns the cost gradient at the current estimate of the offset.
 *
 * afld - pointer afLockData structure. 
 * grad - pre-allocated storage for two elements.
 */
void aflGetCostGradient(afLockData *afld, double *cost)
{
}


/*
 * aflGetMag()
 *
 * Returns the correlation magnitude.
 *
 * afld - pointer afLockData structure.
 * mag - pre-allocated storage for a single element.
 */
void aflGetMag(afLockData *afld, double *mag)
{
  *mag = afld->mag;
}


/*
 * aflGetOffset()
 *
 * Returns the current estimate of the offset.
 *
 * afld - pointer afLockData structure.
 * offset - pre-allocated storage for two elements.
 */
void aflGetOffset(afLockData *afld, double *offset)
{
  offset[0] = afld->dy;
  offset[1] = afld->dx;
}


/*
 * aflGetVector()
 *
 * Used for debugging.
 *
 * afld - pointer afLockData structure.
 * vec - pre-allocated storage for the vector.
 * which - which vector to get.
 */
void aflGetVector(afLockData *afld, double *vec, int which)
{
  int i,j;

  if (which == 0){
    for(i=0;i<(afld->y_size*afld->x_size);i++){
      vec[i] = afld->im1[i];
    }
  }
  else if (which == 1){
    for(i=0;i<(afld->y_size*afld->x_size);i++){
      vec[i] = afld->fft_vector[i];
    }
  }
  else if (which == 2){
    for(i=0;i<afld->y_size;i++){
      for(j=0;j<afld->fft_size;j++){
	vec[i*afld->x_size+j] = afld->fft_vector_fft[i*afld->fft_size+j][0];
      }
    }
  }
  else if (which == 3){
    for(i=0;i<afld->y_size;i++){
      for(j=0;j<afld->fft_size;j++){
	vec[i*afld->x_size+j] = afld->fft_vector_fft[i*afld->fft_size+j][1];
      }
    }
  }
  else if (which == 4){
    for(i=0;i<afld->y_size;i++){
      for(j=0;j<afld->fft_size;j++){
	vec[i*afld->x_size+j] = afld->im2_fft[i*afld->fft_size+j][0];
      }
    }
  }
  else if (which == 5){
    for(i=0;i<afld->y_size;i++){
      for(j=0;j<afld->fft_size;j++){
	vec[i*afld->x_size+j] = afld->im2_fft[i*afld->fft_size+j][1];
      }
    }
  }
}


/*
 * aflInitialize()
 *
 * Initialize auto focus lock fitter.
 *
 * y_size - image size (slow axis), should be a power of 2.
 * x_size - image size (fast axis), should be a power of 2.
 * downsample - downsampling factor, should divide sx and sy.
 */
afLockData *aflInitialize(int y_size, int x_size, int downsample)
{
  int i;
  afLockData *afld;

  afld = (afLockData *)malloc(sizeof(afLockData));

  /*
   * Note that we are zero padding to 2x the size (after downsampling).
   */
  afld->downsample = downsample;
  afld->fft_size = x_size/downsample+1;
  afld->xo = x_size/downsample-1;
  afld->x_size = 2*x_size/downsample;
  afld->yo = y_size/downsample-1;
  afld->y_size = 2*y_size/downsample;

  afld->im1 = (double *)malloc(sizeof(double)*afld->y_size*afld->x_size);
  afld->w1 = (double *)malloc(sizeof(double)*afld->y_size*afld->x_size);
  afld->x_freq = (double *)malloc(sizeof(double)*afld->y_size*afld->x_size);
  afld->y_freq = (double *)malloc(sizeof(double)*afld->y_size*afld->x_size);
  
  afld->fft_vector = (double *)fftw_malloc(sizeof(double)*afld->y_size*afld->x_size);
  afld->fft_vector_fft = (fftw_complex *)fftw_malloc(sizeof(fftw_complex)*afld->y_size*afld->fft_size);
  afld->im2_fft = (fftw_complex *)fftw_malloc(sizeof(fftw_complex)*afld->y_size*afld->fft_size);
  afld->xy_shift = (fftw_complex *)fftw_malloc(sizeof(fftw_complex)*afld->y_size*afld->fft_size);

  afld->fft_forward = fftw_plan_dft_r2c_2d(afld->y_size,
					   afld->x_size,
					   afld->fft_vector,
					   afld->fft_vector_fft,
					   FFTW_MEASURE);

  afld->fft_backward = fftw_plan_dft_c2r_2d(afld->y_size,
					    afld->x_size,
					    afld->fft_vector_fft,
					    afld->fft_vector,
					    FFTW_MEASURE);

  for(i=0;i<(afld->y_size*afld->x_size);i++){
    afld->im1[i] = 0.0;
  }
 
  return afld;
}


/*
 * aflNewImage()
 *
 * New images to find optimal cross-correlation of. This also
 * calculates the initial estimate of the offset.
 *
 * afld - pointer to afLockData structure.
 * image1 - reference image.
 * image2 - other image.
 * bg1 - background to subtract from image1.
 * bg2 - background to subtract from image2.
 */
void aflNewImage(afLockData *afld, double *image1, double *image2, double bg1, double bg2)
{
  int i,j,k,l,m_i,m_j;
  double c,m,r;

  /* Rebin image 1. */
  aflRebin(afld, image1, bg1);

  /* Copy binned image1 into im1. */
  for(i=0;i<(afld->y_size/2);i++){
    for(j=0;j<(afld->x_size/2);j++){
      k = i*afld->x_size+j;
      afld->im1[k] = afld->w1[k];
    }
  }

  /* Zero all elements of fft_vector. */
  for(i=0;i<(afld->y_size*afld->x_size);i++){
    afld->fft_vector[i] = 0.0;
  }
  
  /* Copy binned image1 into fft_vector. */
  for(i=0;i<(afld->y_size/2);i++){
    for(j=0;j<(afld->x_size/2);j++){
      k = i*afld->x_size+j;
      afld->fft_vector[k] = afld->w1[k];
    }
  }
  
  /* FFT */
  fftw_execute(afld->fft_forward);
  
  /* Temporarily store FFT of binned image1 in im2_fft. */
  for(i=0;i<(afld->y_size*afld->fft_size);i++){
    afld->im2_fft[i][0] = afld->fft_vector_fft[i][0];
    afld->im2_fft[i][1] = afld->fft_vector_fft[i][1];
  }

  /* Rebin image 2. */
  aflRebin(afld, image2, bg2);

  /* Flip binned image2 into fft_vector. */
  for(i=0;i<(afld->y_size/2);i++){
    j = (afld->y_size/2)-i-1;
    for(k=0;k<(afld->x_size/2);k++){
      l = (afld->x_size/2)-k-1;
      afld->fft_vector[i*afld->x_size+k] = afld->w1[j*afld->x_size+l];
    }
  }

  /* FFT */
  fftw_execute(afld->fft_forward);
  
  /* Multiply, this cross-correlates binned image1 and binned image2. */
  for(i=0;i<(afld->y_size*afld->fft_size);i++){
    r = afld->im2_fft[i][0]*afld->fft_vector_fft[i][0] - afld->im2_fft[i][1]*afld->fft_vector_fft[i][1];
    c = afld->im2_fft[i][1]*afld->fft_vector_fft[i][0] + afld->im2_fft[i][0]*afld->fft_vector_fft[i][1];
    afld->fft_vector_fft[i][0] = r;
    afld->fft_vector_fft[i][1] = c;    
  }

  /* IFFT */
  fftw_execute(afld->fft_backward);
  
  /* Find maximum cross-correlation. */
  m = afld->fft_vector[0];
  m_i = 0;
  m_j = 0;
  for(i=0;i<afld->y_size;i++){
    for(j=0;j<afld->x_size;j++){
      k = i*afld->x_size+j;
      if(afld->fft_vector[k] > m){
	m = afld->fft_vector[k];
	m_i = i;
	m_j = j;
      }
    }
  }

  afld->dy = (double)(m_i - afld->yo);
  afld->dx = (double)(m_j - afld->xo);
  afld->mag = m/((double)afld->y_size*afld->x_size);

  /* Zero all elements of fft_vector. */
  for(i=0;i<(afld->y_size*afld->x_size);i++){
    afld->fft_vector[i] = 0.0;
  }

  /* Copy binned image2 into fft_vector. */
  for(i=0;i<(afld->y_size/2);i++){
    for(j=0;j<(afld->x_size/2);j++){
      k = i*afld->x_size+j;
      afld->fft_vector[k] = afld->w1[k];
    }
  }
  
  /* FFT */
  fftw_execute(afld->fft_forward);
  
  /* Store FFT of binned image2 in im2_fft. */
  for(i=0;i<(afld->y_size*afld->fft_size);i++){
    afld->im2_fft[i][0] = afld->fft_vector_fft[i][0];
    afld->im2_fft[i][1] = afld->fft_vector_fft[i][1];
  }
}

/*
 * aflRebin()
 *
 * Downsample an image. Downsampled imaged is stored in the w1 array.
 *
 * afld - pointer to afLockData structure.
 * image - image to downsample.
 * bg - background to subtract from image.
 */
void aflRebin(afLockData *afld, double *image, double bg)
{
  int i,j,k,l,xs,ys;
  
  xs = afld->x_size*afld->downsample/2;
  ys = afld->y_size*afld->downsample/2;

  for(i=0;i<(afld->y_size*afld->x_size);i++){
    afld->w1[i] = 0.0;
  }

  for(i=0;i<ys;i++){
    j = i/afld->downsample;
    for(k=0;k<xs;k++){
      l = k/afld->downsample;
      afld->w1[j*afld->x_size+l] += image[i*xs+k] - bg;
    }
  }
}
