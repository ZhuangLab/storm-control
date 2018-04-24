/*
 * Does the lifting for determining focus lock offsets
 * by maximizing the correlation of the image from the
 * focus lock camera with a 2D Gaussian.
 *
 * Hazen 04/18
 *
 *  gcc -fPIC -g -c -Wall multi_fit.c
 *  gcc -shared -Wl,-soname,multi_fit.so.1 -o multi_fit.so.1.0.1 multi_fit.o cubic_spline.o -lc -llapack
 */

/* Include */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>

#define TOLERANCE 1.0e-9

typedef struct corr2DData
{
  int n_checks;       /* Number of checks for stale values. */
  int n_updates;      /* Number of updates. */
  
  int size_x;         /* AOI size in X. */
  int size_y;         /* AOI size in Y. */

  int stale_ddx;      /* Second derivative in X is stale. */
  int stale_ddy;      /* Second derivative in Y is stale. */
  int stale_dx;       /* First derivative in X is stale. */
  int stale_dy;       /* First derivative in Y is stale. */
  int stale_f;        /* Function is stale. */
  int stale_gi;       /* Gaussian image is stale. */

  double cx;          /* X center position. */
  double cy;          /* Y center position. */
  double ddx;         /* Current second derivative in X. */
  double ddy;         /* Current second derivative in Y. */
  double dx;          /* Current first derivative in X. */
  double dy;          /* Current first derivative in Y. */
  double f;           /* Current function value. */
  double last_x;      /* Last X position. */
  double last_y;      /* Last Y position. */
  double sg_term;     /* 1.0/(sigm*sigma). */

  double *g_im;       /* Gaussian image. */
  double *gx;         /* Gaussian in x. */
  double *gy;         /* Gaussian in y. */
  double *r_im;       /* Reference image. */
  double *xi;         /* X index. */
  double *yi;         /* Y index. */
} corr2DData;


void checkStale(corr2DData *, double, double);
void cleanup(corr2DData *);
double ddx(corr2DData *, double, double);
double ddy(corr2DData *, double, double);
double dx(corr2DData *, double, double);
double dy(corr2DData *, double, double);
double fn(corr2DData *, double, double);
void gImage(corr2DData *, double, double);
corr2DData *initialize(double, int, int);
void setImage(corr2DData *, double *);
void setStale(corr2DData *);


/*
 * Check if the position has changed and we need to update.
 */
void checkStale(corr2DData *c2d, double x, double y)
{
  double dx,dy;

  c2d->n_checks += 1;
  
  dx = fabs(c2d->last_x - x);
  dy = fabs(c2d->last_y - y);
  
  if ((dx > TOLERANCE) || (dy > TOLERANCE)){
    setStale(c2d);
    c2d->last_x = x;
    c2d->last_y = y;
  }
}

/*
 * Clean everything up when finished.
 */
void cleanup(corr2DData *c2d)
{
  free(c2d->g_im);
  free(c2d->gx);
  free(c2d->gy);
  free(c2d->r_im);
  free(c2d->xi);
  free(c2d->yi);
  free(c2d);
}

double ddx(corr2DData *c2d, double x, double y)
{
  int i,j,k;
  double ddx,t1;
  double *g_im, *r_im, *xi;
  
  checkStale(c2d, x, y);

  /* Check if we need to do anything. */
  if (c2d->stale_ddx != 0){
    c2d->n_updates += 1;
      
    gImage(c2d, x, y);
    
    ddx = 0.0;
    g_im = c2d->g_im;
    r_im = c2d->r_im;
    xi = c2d->xi;
    for(i=0;i<c2d->size_x;i++){
      j = i*c2d->size_y;
      t1 = (x - xi[i])*c2d->sg_term;
      for(k=0;k<c2d->size_y;k++){
	ddx += g_im[j+k]*r_im[j+k]*(t1*t1 - c2d->sg_term);
      }
    }
    c2d->ddx = ddx;
    c2d->stale_ddx = 0;
  }
  return c2d->ddx;
}

double ddy(corr2DData *c2d, double x, double y)
{
  int i,j,k;
  double ddy,t1;
  double *g_im, *r_im, *yi;
  
  checkStale(c2d, x, y);

  /* Check if we need to do anything. */
  if (c2d->stale_ddy != 0){
    c2d->n_updates += 1;
	
    gImage(c2d, x, y);

    ddy = 0.0;
    g_im = c2d->g_im;
    r_im = c2d->r_im;
    yi = c2d->yi;
    for(i=0;i<c2d->size_y;i++){
      t1 = -(y - yi[i])*c2d->sg_term;
      for(j=0;j<c2d->size_x;j++){
	k = j*c2d->size_y + i;
	ddy += g_im[k]*r_im[k]*(t1*t1 - c2d->sg_term);
      }
    }
    c2d->ddy = ddy;
    c2d->stale_ddy = 0;
  }
  return c2d->ddy;
}

/*
 * Calculate derivative in x.
 */
double dx(corr2DData *c2d, double x, double y)
{
  int i,j,k;
  double dx,t1;
  double *g_im, *r_im, *xi;
  
  checkStale(c2d, x, y);

  /* Check if we need to do anything. */
  if (c2d->stale_dx != 0){
    c2d->n_updates += 1;
	
    gImage(c2d, x, y);

    dx = 0.0;
    g_im = c2d->g_im;
    r_im = c2d->r_im;
    xi = c2d->xi;
    for(i=0;i<c2d->size_x;i++){
      j = i*c2d->size_y;
      t1 = -(x - xi[i])*c2d->sg_term;
      for(k=0;k<c2d->size_y;k++){
	dx += g_im[j+k]*r_im[j+k]*t1;
      }
    }
    c2d->dx = dx;
    c2d->stale_dx = 0;
  }
  return c2d->dx;
}

/*
 * Calculate derivative in y.
 */
double dy(corr2DData *c2d, double x, double y)
{
  int i,j,k;
  double dy,t1;
  double *g_im, *r_im, *yi;
  
  checkStale(c2d, x, y);

  /* Check if we need to do anything. */
  if (c2d->stale_dy != 0){
    c2d->n_updates += 1;
	
    gImage(c2d, x, y);

    dy = 0.0;
    g_im = c2d->g_im;
    r_im = c2d->r_im;
    yi = c2d->yi;
    for(i=0;i<c2d->size_y;i++){
      t1 = -(y - yi[i])*c2d->sg_term;
      for(j=0;j<c2d->size_x;j++){
	k = j*c2d->size_y + i;
	dy += g_im[k]*r_im[k]*t1;
      }
    }
    c2d->dy = dy;
    c2d->stale_dy = 0;
  }
  return c2d->dy;  
}

/*
 * Calculate function.
 */
double fn(corr2DData *c2d, double x, double y)
{
  int i;
  double f;
  double *g_im, *r_im;
  
  checkStale(c2d, x, y);

  /* Check if we need to do anything. */
  if (c2d->stale_f != 0){
    c2d->n_updates += 1;
	
    gImage(c2d, x, y);

    f = 0.0;
    g_im = c2d->g_im;
    r_im = c2d->r_im;
    for(i=0;i<(c2d->size_x*c2d->size_y);i++){
      f += g_im[i]*r_im[i];
    }
    c2d->f = f;
    c2d->stale_f = 0;
  }
  return c2d->f;
}

/*
 * Calculate image of Gaussian at x,y.
 */
void gImage(corr2DData *c2d, double x, double y)
{
  int i,j,k;
  double dd;
  double *gx,*gy;

  /* Check if we need to do anything. */
  if (c2d->stale_gi == 0){
    return;
  }

  gx = c2d->gx;
  gy = c2d->gy;
  
  for(i=0;i<c2d->size_x;i++){
    dd = c2d->xi[i] - x;
    dd = -0.5 * dd * dd * c2d->sg_term;
    gx[i] = exp(dd);
  }

  for(i=0;i<c2d->size_y;i++){
    dd = c2d->yi[i] - y;
    dd = -0.5 * dd * dd * c2d->sg_term;
    gy[i] = exp(dd);
  }

  for(i=0;i<c2d->size_x;i++){
    j = i*c2d->size_y;
    for(k=0;k<c2d->size_y;k++){
      c2d->g_im[j+k] = gx[i]*gy[k];
    }
  }

  c2d->stale_gi = 0;
}

/*
 * Initialize.
 */
corr2DData *initialize(double sigma, int sx, int sy)
{
  int i;
  double start;
  corr2DData* c2d;

  c2d = (corr2DData *)malloc(sizeof(corr2DData));
  
  c2d->n_checks = 0;
  c2d->n_updates = 0;
      
  c2d->size_x = sx;
  c2d->size_y = sy;

  c2d->last_x = 0.0;
  c2d->last_y = 0.0;
  c2d->sg_term = 1.0/(sigma*sigma);
  
  c2d->g_im = (double *)malloc(sizeof(double)*sx*sy);
  c2d->gx = (double *)malloc(sizeof(double)*sx);
  c2d->gy = (double *)malloc(sizeof(double)*sy);
  c2d->r_im = (double *)malloc(sizeof(double)*sx*sy);
  c2d->xi = (double *)malloc(sizeof(double)*sx);
  c2d->yi = (double *)malloc(sizeof(double)*sy);

  /* Gaussian center position. */
  c2d->cx = 0.5 * ((double)sx) - 0.5;
  c2d->cy = 0.5 * ((double)sy) - 0.5;

  /* Initialize index arrays. */
  start = -0.5 * ((double)sx);
  for(i=0;i<sx;i++){
    c2d->xi[i] = start + (double)i + 0.5;
  }
  
  start = -0.5 * ((double)sy);
  for(i=0;i<sy;i++){
    c2d->yi[i] = start + (double)i + 0.5;
  }
  
  setStale(c2d);
  
  return c2d;
}

/*
 * Set the image to correlate to.
 */
void setImage(corr2DData *c2d, double *im)
{
  int i;

  for(i=0;i<(c2d->size_x*c2d->size_y);i++){
    c2d->r_im[i] = im[i];
  }
  setStale(c2d);
}

/*
 * Set all the stale markers to True.
 */
void setStale(corr2DData *c2d)
{
  c2d->stale_ddx = 1;
  c2d->stale_ddy = 1;
  c2d->stale_dx = 1;
  c2d->stale_dy = 1;
  c2d->stale_f = 1;
  c2d->stale_gi = 1;
}
