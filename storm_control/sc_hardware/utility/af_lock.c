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
#include <stdint.h>
#include <string.h>
#include <math.h>

#include <fftw3.h>


/* Defines */
#define AF_SUCCESS 0
#define AF_MAXITERS -1
#define AF_NOTSOLVABLE -2


/* Structures & Types */
typedef struct afLockData {
  int downsample;
  int fft_size;
  int xo;
  int x_size;
  int yo;
  int y_size;

  double cost;
  double dx;
  double dy;
  double mag;
  double norm;

  double *cost_grad;
  double *cost_hess;
  double *fft_vector;
  double *im1;
  double *w1;
  double *x_shift;
  double *x_r;
  double *x_c;
  double *y_shift;
  double *y_r;
  double *y_c;
  
  fftw_plan fft_backward;
  fftw_plan fft_forward;

  fftw_complex *fft_vector_fft;
  fftw_complex *im2_fft;
  fftw_complex *im2_fft_shift;
} afLockData;


int aflCalcShift(afLockData *, double, double);
int aflCleanup(afLockData *);
int aflCost(afLockData *, double, double);
int aflCostGradient(afLockData *, double, double);
int aflCostHessian(afLockData *, double, double);
int aflGetCost(afLockData *, double *);
int aflGetCostGradient(afLockData *, double *);
int aflGetCostHessian(afLockData *, double *);
int aflGetMag(afLockData *, double *);
int aflGetOffset(afLockData *, double *);
int aflGetVector(afLockData *, double *, int);
afLockData *aflInitialize(int, int, int);
int aflMinimizeNM(afLockData *, double, int);
int aflNewImage(afLockData *, double *, double *, double, double);
void aflNewImageStep1(afLockData *);
void aflNewImageStep2(afLockData *);
int aflNewImageU16(afLockData *, uint16_t *, double);
int aflRebin(afLockData *, double *, double);
int aflRebinU16(afLockData *, uint16_t *, double);
int aflSolveStep(afLockData *, double *);


/*
 * aflCalcShift()
 *
 * Calculate shift vector at current offset estimate.
 * 
 * afld - pointer to a afLockData structure.
 */
int aflCalcShift(afLockData *afld, double dy, double dx)
{
  int i,j,k;
  double r;
  double c;

  if((dy!=afld->dy)||(dx!=afld->dx)){
    afld->dy = dy;
    afld->dx = dx;

    /* Calculate shift vectors. */
    for(i=0;i<afld->y_size;i++){
      afld->y_r[i] = cos(afld->y_shift[i]*dy);
    }
    for(i=0;i<afld->y_size;i++){
      afld->y_c[i] = sin(afld->y_shift[i]*dy);
    }
    for(i=0;i<afld->fft_size;i++){
      afld->x_r[i] = cos(afld->x_shift[i]*dx);
    }
    for(i=0;i<afld->fft_size;i++){
      afld->x_c[i] = sin(afld->x_shift[i]*dx);
    }

    /* Calculate im2 shift. */
    for(i=0;i<afld->y_size;i++){
      for(j=0;j<afld->fft_size;j++){
	k = i*afld->fft_size+j;
	r = afld->y_r[i]*afld->x_r[j] - afld->y_c[i]*afld->x_c[j];
	c = afld->y_r[i]*afld->x_c[j] + afld->y_c[i]*afld->x_r[j];
	afld->im2_fft_shift[k][0] = r*afld->im2_fft[k][0] - c*afld->im2_fft[k][1];
	afld->im2_fft_shift[k][1] = c*afld->im2_fft[k][0] + r*afld->im2_fft[k][1];
      }
    }
  }

  return AF_SUCCESS;
}


/*
 * aflCleanup()
 *
 * Clean up auto focus lock fitter.
 * 
 * afld - pointer to a afLockData structure.
 */
int aflCleanup(afLockData *afld)
{
  free(afld->cost_grad);
  free(afld->cost_hess);
  free(afld->im1);
  free(afld->w1);
  free(afld->x_shift);
  free(afld->x_r);
  free(afld->x_c);
  free(afld->y_shift);
  free(afld->y_r);
  free(afld->y_c);

  fftw_free(afld->fft_vector);
  fftw_free(afld->fft_vector_fft);
  fftw_free(afld->im2_fft);
  fftw_free(afld->im2_fft_shift);
  
  fftw_destroy_plan(afld->fft_forward);
  fftw_destroy_plan(afld->fft_backward);
  
  free(afld);

  return AF_SUCCESS;
}


/*
 * aflCost()
 *
 * Calculate cost.
 *
 * afld - pointer to a afLockData structure.
 */
int aflCost(afLockData *afld, double dy, double dx)
{
  int i;
  double sum;

  /* Update shift. */
  aflCalcShift(afld, dy, dx);

  /* Copy into IFFT. */
  memcpy(afld->fft_vector_fft, afld->im2_fft_shift, sizeof(fftw_complex)*afld->y_size*afld->fft_size);
  
  /* IFFT */
  fftw_execute(afld->fft_backward);

  /* Compute dot product. */
  sum = 0.0;
  for(i=0;i<(afld->y_size*afld->x_size);i++){
    sum += afld->im1[i]*afld->fft_vector[i];
  }

  /* Store current cost. */
  afld->cost = -sum*afld->norm;

  return AF_SUCCESS;
}


/*
 * aflCostGradient()
 *
 * Calculate gradient of cost.
 *
 * afld - pointer to a afLockData structure.
 */
int aflCostGradient(afLockData *afld, double dy, double dx)
{
  int i,j,k;
  double sum;

  /* Update shift. */
  aflCalcShift(afld, dy, dx);

  /* Multiply by y-shift and copy into IFFT. */
  for(i=0;i<afld->y_size;i++){
    for(j=0;j<afld->fft_size;j++){
      k = i*afld->fft_size+j;
      afld->fft_vector_fft[k][0] = -afld->im2_fft_shift[k][1] * afld->y_shift[i];
      afld->fft_vector_fft[k][1] =  afld->im2_fft_shift[k][0] * afld->y_shift[i];
    }
  }
 
  /* IFFT */
  fftw_execute(afld->fft_backward);

  /* Compute dot product. */
  sum = 0.0;
  for(i=0;i<(afld->y_size*afld->x_size);i++){
    sum += afld->im1[i]*afld->fft_vector[i];
  }

  /* Store y cost derivative. */
  afld->cost_grad[0] = -sum*afld->norm;

  /* Multiply by x-shift and copy into IFFT. */
  for(i=0;i<afld->y_size;i++){
    for(j=0;j<afld->fft_size;j++){
      k = i*afld->fft_size+j;
      afld->fft_vector_fft[k][0] = -afld->im2_fft_shift[k][1] * afld->x_shift[j];
      afld->fft_vector_fft[k][1] =  afld->im2_fft_shift[k][0] * afld->x_shift[j];
    }
  }
 
  /* IFFT */
  fftw_execute(afld->fft_backward);

  /* Compute dot product. */
  sum = 0.0;
  for(i=0;i<(afld->y_size*afld->x_size);i++){
    sum += afld->im1[i]*afld->fft_vector[i];
  }

  /* Store x cost derivative. */
  afld->cost_grad[1] = -sum*afld->norm;

  return AF_SUCCESS;
}


/*
 * aflCostHessian()
 *
 * Calculate hessian of cost.
 *
 * afld - pointer to a afLockData structure.
 */
int aflCostHessian(afLockData *afld, double dy, double dx)
{
  int i,j,k;
  double sum;

  /* Update shift. */
  aflCalcShift(afld, dy, dx);

  /* Multiply by y-shift * y-shift and copy into IFFT. */
  for(i=0;i<afld->y_size;i++){
    for(j=0;j<afld->fft_size;j++){
      k = i*afld->fft_size+j;
      afld->fft_vector_fft[k][0] = -afld->im2_fft_shift[k][0] * afld->y_shift[i] * afld->y_shift[i];
      afld->fft_vector_fft[k][1] = -afld->im2_fft_shift[k][1] * afld->y_shift[i] * afld->y_shift[i];
    }
  }
 
  /* IFFT */
  fftw_execute(afld->fft_backward);

  /* Compute dot product. */
  sum = 0.0;
  for(i=0;i<(afld->y_size*afld->x_size);i++){
    sum += afld->im1[i]*afld->fft_vector[i];
  }

  /* Store cost dy * dy. */
  afld->cost_hess[0] = -sum*afld->norm;

  
  /* Multiply by y-shift * x-shift and copy into IFFT. */
  for(i=0;i<afld->y_size;i++){
    for(j=0;j<afld->fft_size;j++){
      k = i*afld->fft_size+j;
      afld->fft_vector_fft[k][0] = -afld->im2_fft_shift[k][0] * afld->y_shift[i] * afld->x_shift[j];
      afld->fft_vector_fft[k][1] = -afld->im2_fft_shift[k][1] * afld->y_shift[i] * afld->x_shift[j];
    }
  }
 
  /* IFFT */
  fftw_execute(afld->fft_backward);

  /* Compute dot product. */
  sum = 0.0;
  for(i=0;i<(afld->y_size*afld->x_size);i++){
    sum += afld->im1[i]*afld->fft_vector[i];
  }

  /* Store cost dy * dx and dx * dy */
  afld->cost_hess[1] = -sum*afld->norm;
  afld->cost_hess[2] = afld->cost_hess[1];
  
  /* Multiply by x-shift * x-shift and copy into IFFT. */
  for(i=0;i<afld->y_size;i++){
    for(j=0;j<afld->fft_size;j++){
      k = i*afld->fft_size+j;
      afld->fft_vector_fft[k][0] = -afld->im2_fft_shift[k][0] * afld->x_shift[j] * afld->x_shift[j];
      afld->fft_vector_fft[k][1] = -afld->im2_fft_shift[k][1] * afld->x_shift[j] * afld->x_shift[j];
    }
  }
 
  /* IFFT */
  fftw_execute(afld->fft_backward);

  /* Compute dot product. */
  sum = 0.0;
  for(i=0;i<(afld->y_size*afld->x_size);i++){
    sum += afld->im1[i]*afld->fft_vector[i];
  }

  /* Store cost dx * dx. */
  afld->cost_hess[3] = -sum*afld->norm;

  return AF_SUCCESS;
}


/*
 * aflGetCost()
 *
 * Returns the cost at the current estimate of the offset.
 *
 * afld - pointer afLockData structure.
 * cost - pre-allocated storage for a single element.
 */
int aflGetCost(afLockData *afld, double *cost)
{
  *cost = afld->cost;

  return AF_SUCCESS;
}


/*
 * aflGetCostGradient()
 *
 * Returns the cost gradient at the current estimate of the offset.
 *
 * afld - pointer afLockData structure. 
 * grad - pre-allocated storage for two elements.
 */
int aflGetCostGradient(afLockData *afld, double *grad)
{
  grad[0] = afld->cost_grad[0];
  grad[1] = afld->cost_grad[1];

  return AF_SUCCESS;
}


/*
 * aflGetCostHessian()
 *
 * Returns the cost hessian at the current estimate of the offset.
 *
 * afld - pointer afLockData structure. 
 * hess - pre-allocated storage for four elements.
 */
int aflGetCostHessian(afLockData *afld, double *hess)
{
  int i;

  for(i=0;i<4;i++){
    hess[i] = afld->cost_hess[i];
  }

  return AF_SUCCESS;
}


/*
 * aflGetMag()
 *
 * Returns the correlation magnitude.
 *
 * afld - pointer afLockData structure.
 * mag - pre-allocated storage for a single element.
 */
int aflGetMag(afLockData *afld, double *mag)
{
  *mag = afld->mag;

  return AF_SUCCESS;
}


/*
 * aflGetOffset()
 *
 * Returns the current estimate of the offset.
 *
 * afld - pointer afLockData structure.
 * offset - pre-allocated storage for two elements.
 */
int aflGetOffset(afLockData *afld, double *offset)
{
  offset[0] = afld->dy;
  offset[1] = afld->dx;

  return AF_SUCCESS;
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
int aflGetVector(afLockData *afld, double *vec, int which)
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
  else if (which == 6){
    for(i=0;i<afld->y_size;i++){
      for(j=0;j<afld->fft_size;j++){
	vec[i*afld->x_size+j] = afld->x_shift[j];
      }
    }
  }
  else if (which == 7){
    for(i=0;i<afld->y_size;i++){
      for(j=0;j<afld->fft_size;j++){
	vec[i*afld->x_size+j] = afld->y_shift[i];
      }
    }
  }

  return AF_SUCCESS;
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
  double dfx,dfy;
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
  afld->norm = 1.0/((double)afld->x_size*afld->y_size);
    
  afld->cost_grad = (double *)malloc(sizeof(double)*2);
  afld->cost_hess = (double *)malloc(sizeof(double)*4);
  afld->im1 = (double *)malloc(sizeof(double)*afld->y_size*afld->x_size);
  afld->w1 = (double *)malloc(sizeof(double)*afld->y_size*afld->x_size);
  afld->x_shift = (double *)malloc(sizeof(double)*afld->fft_size);
  afld->x_r = (double *)malloc(sizeof(double)*afld->fft_size);
  afld->x_c = (double *)malloc(sizeof(double)*afld->fft_size);
  afld->y_shift = (double *)malloc(sizeof(double)*afld->y_size);
  afld->y_r = (double *)malloc(sizeof(double)*afld->y_size);
  afld->y_c = (double *)malloc(sizeof(double)*afld->y_size);
  
  afld->fft_vector = (double *)fftw_malloc(sizeof(double)*afld->y_size*afld->x_size);
  afld->fft_vector_fft = (fftw_complex *)fftw_malloc(sizeof(fftw_complex)*afld->y_size*afld->fft_size);
  afld->im2_fft = (fftw_complex *)fftw_malloc(sizeof(fftw_complex)*afld->y_size*afld->fft_size);
  afld->im2_fft_shift = (fftw_complex *)fftw_malloc(sizeof(fftw_complex)*afld->y_size*afld->fft_size);

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

  /* Zero storage for binned im1. */
  for(i=0;i<(afld->y_size*afld->x_size);i++){
    afld->im1[i] = 0.0;
  }

  /* Initialize FFT shift arrays. */
  dfy = 1.0/afld->y_size;
  for(i=0;i<(afld->y_size/2);i++){
    afld->y_shift[i] = -2.0*M_PI*dfy*(double)i;
  }
  for(i=1;i<(afld->y_size/2+1);i++){
    afld->y_shift[afld->y_size-i] = 2.0*M_PI*dfy*(double)i;
  }
  
  dfx = 1.0/afld->x_size;
  for(i=0;i<afld->fft_size;i++){
    afld->x_shift[i] = -2.0*M_PI*dfx*(double)i;
  }
  afld->x_shift[(afld->fft_size-1)] = -1.0*afld->x_shift[(afld->fft_size-1)];
  
  return afld;
}


/*
 * aflMinimizeNM()
 *
 * Solve for optimal offset using Newton's method.
 *
 * afld - pointer to a afLockData structure.
 * step_tol - step size at convergence.
 * max_iters - maximum iterations.
 */
int aflMinimizeNM(afLockData *afld, double step_tol, int max_iters)
{
  int i,ret;
  double dx, dy, step_norm, t1;
  double step[2];

  i = 0;
  t1 = step_tol*step_tol;
  dx = afld->dx;
  dy = afld->dy;
  while (i < max_iters){

    /* Calculate gradient and Hessian. */
    aflCostGradient(afld, dy, dx);
    aflCostHessian(afld, dy, dx);

    /* Calculate step vector. */
    ret = aflSolveStep(afld, step);
    if (ret != AF_SUCCESS){
      return ret;
    }

    /* Update. */
    dx -= step[1];
    dy -= step[0]; 
    
    /* Check for convergence. */
    step_norm = step[0]*step[0] + step[1]*step[1];
    if (step_norm < t1){
      afld->dx = dx; 
      afld->dy = dy;
      return AF_SUCCESS;
    }
    
    i++;
  }

  return AF_MAXITERS;
}


/*
 * aflNewImage()
 *
 * New images to find optimal cross-correlation of. This also
 * calculates the initial estimate of the offset.
 *
 * As the processing is the same, only the rebin is different
 * we have factored out the processing into the aflNewImageStepX()
 * functions.
 *
 * afld - pointer to afLockData structure.
 * image1 - reference image.
 * image2 - other image.
 * bg1 - background to subtract from image1.
 * bg2 - background to subtract from image2.
 */
int aflNewImage(afLockData *afld, double *image1, double *image2, double bg1, double bg2)
{
  /* Rebin image 1. */
  aflRebin(afld, image1, bg1);

  /* Step 1.*/
  aflNewImageStep1(afld);

  /* Rebin image 2. */
  aflRebin(afld, image2, bg2);

  /* Step 2.*/
  aflNewImageStep2(afld);

  return AF_SUCCESS;
}


/*
 * aflNewImageStep1()
 *
 * Perform step1 of the new image logic.
 *
 * afld - pointer to afLockData structure.
 */
void aflNewImageStep1(afLockData *afld)
{
  int i,j,k;

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
  memcpy(afld->im2_fft, afld->fft_vector_fft, sizeof(fftw_complex)*afld->y_size*afld->fft_size);
}


/*
 * aflNewImageStep2()
 *
 * Perform step2 of the new image logic.
 *
 * afld - pointer to afLockData structure.
 */
void aflNewImageStep2(afLockData *afld)
{
  int i,j,k,l,m_i,m_j;
  double c,dx,dy,m,r;

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

  dy = (double)(m_i - afld->yo);
  dx = (double)(m_j - afld->xo);

  afld->dy = dy + 1.0;
  afld->dx = dx + 1.0;

  afld->mag = m*afld->norm;

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
  memcpy(afld->im2_fft, afld->fft_vector_fft, sizeof(fftw_complex)*afld->y_size*afld->fft_size);

  /* Initialize shift vectors. */
  aflCalcShift(afld, dy, dx);
}


/*
 * aflNewImageU16()
 *
 * This is the unsigned 16 bit integer version of aflNewImage(). It also
 * expects a single image.
 *
 * afld - pointer to afLockData structure.
 * image - combined image1 and image2 in first & second half of image.
 * bg1 - background to subtract from image1.
 * bg2 - background to subtract from image2.
 */
int aflNewImageU16(afLockData *afld, uint16_t *image, double bg)
{
  int i2_offset;

  /* Rebin image 1. */
  aflRebinU16(afld, image, bg);

  /* Step 1.*/
  aflNewImageStep1(afld);

  /* Rebin image 2. */
  i2_offset = (afld->x_size*afld->y_size*afld->downsample*afld->downsample/4);
  aflRebinU16(afld, image + i2_offset, bg);

  /* Step 2.*/
  aflNewImageStep2(afld);

  return AF_SUCCESS;
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
int aflRebin(afLockData *afld, double *image, double bg)
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

  return AF_SUCCESS;
}


/*
 * aflRebinU16()
 *
 * Downsample an image (uint16 version). Downsampled imaged is stored 
 * in the w1 array.
 *
 * afld - pointer to afLockData structure.
 * image - image to downsample.
 * bg - background to subtract from image.
 */
int aflRebinU16(afLockData *afld, uint16_t *image, double bg)
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
      afld->w1[j*afld->x_size+l] += (double)image[i*xs+k] - bg;
    }
  }

  return AF_SUCCESS;
}


/*
 * aflSolveStep()
 *
 * Solve for step given current Hessian and gradient.
 *
 * Note: This assumes that H[0,1] == H[1,0].
 *
 * afld - pointer to afLockData structure.
 * step - storage for step.
 */
int aflSolveStep(afLockData *afld, double *step)
{
  double t1;

  if (afld->cost_hess[0] == 0.0){
    return AF_NOTSOLVABLE;
  }

  t1 = (-(afld->cost_hess[1]*afld->cost_hess[1])/afld->cost_hess[0] + afld->cost_hess[3]);
  if (t1 == 0.0){
    return AF_NOTSOLVABLE;
  }

  step[1] = (afld->cost_grad[1] - afld->cost_hess[1]*afld->cost_grad[0]/afld->cost_hess[0])/t1;
  step[0] = (afld->cost_grad[0] - afld->cost_hess[1]*step[1])/afld->cost_hess[0];

  return AF_SUCCESS;
}
