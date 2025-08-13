#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


# Requires:
# https://github.com/ludwigschwardt/katbeam
# https://pypi.org/project/scikit-ued/


import glob
import numpy as np
import os
import sys
import time
from astropy.io import fits
from katbeam import JimBeam
from multiprocessing import Pool
from shutil import copyfile
from skued import azimuthal_average as aa


def get_header(fitsfile):
    inphdu = fits.open(fitsfile)
    inphdr = inphdu[0].header
    nx = inphdr.get('NAXIS1')
    ny = inphdr.get('NAXIS2')
    dx = inphdr.get('CDELT1')
    dy = inphdr.get('CDELT2')
    freq = inphdr.get('CRVAL3')
    return nx,ny,dx,dy,freq


def get_image(fitsfile):
    input_hdu = fits.open(fitsfile)[0]
    if len(input_hdu.data.shape) == 2:
            image = np.array(input_hdu.data[:,:])
    elif len(input_hdu.data.shape) == 3:
            image = np.array(input_hdu.data[0,:,:])
    else:
            image = np.array(input_hdu.data[0,0,:,:])
    return image


def flush_fits(newimage,fitsfile):
    f = fits.open(fitsfile,mode='update')
    input_hdu = f[0]
    if len(input_hdu.data.shape) == 2:
            input_hdu.data[:,:] = newimage
    elif len(input_hdu.data.shape) == 3:
            input_hdu.data[0,:,:] = newimage
    else:
            input_hdu.data[0,0,:,:] = newimage
    f.flush()


def makewt(input_fits):
    # Params
    pbcut = 0.3
    beam_model = 'MKAT-AA-L-JIM-2020'
    wt_fits = input_fits.replace('.fits','.wt.fits')
    pbcor_fits = input_fits.replace('.fits','.pbcor.fits')
    if not os.path.isfile(wt_fits) and not os.path.isfile(pbcor_fits):
    # Setup beam model and apply pbcut
    beam = JimBeam(beam_model)
    nx,ny,dx,dy,fitsfreq = get_header(input_fits)
    extent = nx*dx # degrees
    freq = fitsfreq/1e6
    interval = np.linspace(-extent/2.0,extent/2.0,nx)
    xx,yy = np.meshgrid(interval,interval)
    beam_image = beam.I(xx,yy,freq)
    mask = beam_image < pbcut
    beam_image[mask] = np.nan

    ny, nx = beam_image.shape
    x0, y0 = nx // 2, ny // 2
    radius, average = aa(beam_image, center=(x0, y0)) 
    yy, xx = np.ogrid[:ny, :nx]
    r = np.hypot(yy - y0, xx - x0)          
    idx = np.clip(r.astype(np.int32), 0, len(average) - 1)
    beam_image[...] = average[idx]         

    # # Apply azimuthal averaging
    # x0 = int(nx/2)
    # y0 = int(ny/2)
    # radius,average = aa(beam_image,center=(x0,y0))
    # # This can probably be sped up...
    # for y in range(0,ny):
    #     for x in range(0,nx):
    #         val = (((float(y)-y0)**2.0)+((float(x)-x0)**2.0))**0.5
    #         beam_image[y][x] = average[int(val)]

    # Correct image and write out FITS files
    copyfile(input_fits,wt_fits)
    flush_fits(beam_image**2.0,wt_fits)
    print('Processed '+input_fits)



if __name__ == "__main__":

    dirlist = ['XMMLSS_10_7_CUBE_r0p0/',
        'XMMLSS_10_7_CUBE_r0p0/',
        'XMMLSS_10_7_CUBE_r0p5/',
        'XMMLSS_11_7_CUBE_r0p5/',
        'XMMLSS_9_7_CUBE_r0p5/',
        'XMMLSS_9_9_CUBE_r0p5/']

#    pattern = sys.argv[1]

    j = 30

    for indir in dirlist:
        os.chdir(indir)
        fitslist = sorted(glob.glob('*image.fits'))
        pool = Pool(processes=j)
        pool.map(makewt,fitslist)
        os.chdir('../')
