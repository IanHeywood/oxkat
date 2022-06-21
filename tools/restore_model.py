#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import glob
import logging
import numpy
import os
import random 
import scipy.signal
import shutil
import string
import sys

from astropy.io import fits
from astropy.convolution import convolve,Gaussian2DKernel
from itertools import repeat
from multiprocessing import Pool


def get_image(fitsfile):
        input_hdu = fits.open(fitsfile)[0]
        if len(input_hdu.data.shape) == 2:
                image = numpy.array(input_hdu.data[:,:])
        elif len(input_hdu.data.shape) == 3:
                image = numpy.array(input_hdu.data[0,:,:])
        elif len(input_hdu.data.shape) == 4:
                image = numpy.array(input_hdu.data[0,0,:,:])
        else:
                image = numpy.array(input_hdu.data[0,0,0,:,:])
        return image


def flush_fits(newimage,fitsfile):
        f = fits.open(fitsfile,mode='update')
        input_hdu = f[0]
        if len(input_hdu.data.shape) == 2:
                input_hdu.data[:,:] = newimage
        elif len(input_hdu.data.shape) == 3:
                input_hdu.data[0,:,:] = newimage_
        elif len(input_hdu.data.shape) == 4:
                input_hdu.data[0,0,:,:] = newimage
        else:
                input_hdu.data[0,0,0,:,:] = newimage
        f.flush()


def deg2rad(xx):
    return numpy.pi*xx/180.0


def get_header(fitsfile):
    input_hdu = fits.open(fitsfile)[0]
    hdr = input_hdu.header
    bmaj = hdr.get('BMAJ')
    bmin = hdr.get('BMIN')
    bpa = hdr.get('BPA')
    pixscale = hdr.get('CDELT2')
    return bmaj,bmin,bpa,pixscale


def beam_header(fitsfile,bmaj,bmin,bpa):
        outhdu = fits.open(fitsfile,mode='update')
        outhdr = outhdu[0].header
        outhdr.set('BMAJ',bmaj,after='BUNIT')
        outhdr.set('BMIN',bmin,after='BMAJ')
        outhdr.set('BPA',bpa,after='BMIN')
        outhdr.remove('HISTORY')
        outhdu.flush()  


def convolve_fits(residual_fits,model_image,proc_id):

        proc_id = str(proc_id)

        # Set up FITS files
        psf_fits = residual_fits.replace('image','psf')
        restored_fits = residual_fits.replace('image','image-restored')
        shutil.copyfile(residual_fits,restored_fits)


        # Get the fitted beam
        bmaj,bmin,bpa,pixscale = get_header(psf_fits)

        logging.info('(File '+proc_id+') Residual    : '+residual_fits)
        logging.info('(File '+proc_id+') PSF         : '+psf_fits)
        logging.info('(File '+proc_id+') Restored    : '+restored_fits)
        logging.info('(File '+proc_id+') Fitted bmaj : '+str(bmaj*3600))
        logging.info('(File '+proc_id+') Fitted bmin : '+str(bmin*3600))
        logging.info('(File '+proc_id+') Fitted bpa  : '+str(bpa))

        # Create restoring beam image
        xstd = bmin/(2.3548*pixscale)
        ystd = bmaj/(2.3548*pixscale)
        theta = deg2rad(bpa)
        restoring = Gaussian2DKernel(x_stddev=xstd,y_stddev=ystd,theta=theta,x_size=cropsize,y_size=cropsize,mode='center')
        restoring_beam_image = restoring.array
        restoring_beam_image = restoring_beam_image / numpy.max(restoring_beam_image)

        # Convolve model with restoring beam
        model_conv_image = scipy.signal.fftconvolve(model_image, restoring_beam_image, mode='same')

        # Open residual image and add convolved model
        residual_image = get_image(residual_fits)
        restored_image = residual_image + model_conv_image

        # Flush restored FITS file and fix the header
        flush_fits(restored_image,restored_fits)
        beam_header(restored_fits,bmaj,bmin,bpa)


if __name__ == '__main__':

        if len(sys.argv) == 1:
                print('Please specify model FITS image')
                sys.exit()

        logfile = 'restore_model.log'
        logging.basicConfig(filename=logfile, level=logging.DEBUG, format='%(asctime)s |  %(message)s', datefmt='%d/%m/%Y %H:%M:%S ')

        model_fits = sys.argv[1]

        j = 1 # Number of parallel convolutions
        cropsize = 51 # Size of kernel thumbnail
        fits_list = sorted(glob.glob('*image.fits')) # List of residuals
        ids = numpy.arange(0,len(fits_list))

        # Get the image size from first image in list and create matched model image
        img0 = get_image(fits_list[0])
        nx,ny = numpy.shape(img0)
        if nx != ny:
                print('Only square images are supported at present')
                sys.exit()
        tmpmodel_fits = 'temp_model_'+''.join(random.choices(string.ascii_uppercase + string.digits, k=16))+'.fits'
        os.system('fitstool.py -z '+str(nx)+' -o '+tmpmodel_fits+' '+model_fits)
        model_image = get_image(tmpmodel_fits)

        for i in range(0,len(fits_list)):
                convolve_fits(fits_list[i],model_image,ids[i])

        # pool = Pool(processes=j)
        # pool.starmap(convolve_fits,zip(fits_list,repeat(model_image),ids))

