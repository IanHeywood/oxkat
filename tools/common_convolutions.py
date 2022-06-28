#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import glob
import logging
import numpy
import os
import scipy.signal
import shutil
import sys

from astropy import wcs
from astropy.convolution import convolve,Gaussian2DKernel
from astropy.io import fits
from datetime import datetime
from optparse import OptionParser


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


def drop_deg(fitsfile):
    f = fits.open(fitsfile)
    data = f[0].data.squeeze() 
    hdr = f[0].header
    inpwcs = wcs.WCS(hdr).celestial
    hdr1 = inpwcs.to_header()
    f1 = fits.PrimaryHDU(data = data, header = hdr1)
    f1.writeto(fitsfile,overwrite = True)


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



if __name__ == '__main__':


    parser = OptionParser(usage = '%prog [options]')
    parser.add_option('--restored', dest = 'restored_fits', help = 'Name of restored image')
    parser.add_option('--residual', dest = 'residual_fits', default = '', help = 'Name of residual image (default = detect based on restored)')
    parser.add_option('--model', dest = 'model_fits', default = '', help = 'Name of model image (default = detect based on model)')
    parser.add_option('--output', dest = 'restored_conv_fits', default = '', help = 'Name of convolved output image (default = based on restored)')
    parser.add_option('--bmaj', dest = 'target_bmaj', default = '', help = 'Target beam major axis in arcseconds')
    parser.add_option('--bmin', dest = 'target_bmin', default = '', help = 'Target beam minor axis in arcseconds (default = bmaj)')
    parser.add_option('--bpa', dest = 'target_bpa', default = '', help = 'Target beam position angle in degrees east of north (default = 0)')
    parser.add_option('--template', dest = 'template_fits', default = '', help = 'Template FITS image to store rendered beams')
    parser.add_option('--cropsize', dest = 'cropsize', default = 51, help = 'Size of beam template image in pixels (default = 51)')
    parser.add_option('--auto', dest = 'auto', default = 'wsclean', help = 'Set to wsclean or ddfacet to deduce filenames (default = wsclean)')           
    parser.add_option('-f', dest = 'overwrite', action = 'store_true', default = False, help = 'Overwrite existing outputs (default = do not overwrite)')
    parser.add_option('-l', dest = 'initlogfile', action = 'store_true', default = False, help = 'Initialise log file on each run (default = do not initialise)')
    parser.add_option('-c', dest = 'clearup', action = 'store_true', default = False, help = 'Remove intermediate products (default = do not remove)')


    (options,args) = parser.parse_args()
    restored_fits = options.restored_fits
    residual_fits = options.residual_fits
    model_fits = options.model_fits
    restored_conv_fits = options.restored_conv_fits
    target_bmaj = options.target_bmaj
    target_bmin = options.target_bmin
    target_bpa = options.target_bpa
    template_fits = options.template_fits
    cropsize = int(options.cropsize)
    auto = options.auto
    overwrite = options.overwrite
    initlogfile = options.initlogfile
    clearup = options.clearup


    now = datetime.now()
    timestamp = now.strftime('%m-%d-%Y-%H-%M-%S')
    logfile = restored_fits.replace('.fits','-convolutions.log')
    if initlogfile and os.path.isfile(logfile):
        os.remove(logfile)
    logging.basicConfig(filename=logfile, level=logging.DEBUG, format='%(asctime)s |  %(message)s', datefmt='%d/%m/%Y %H:%M:%S ')
    logging.getLogger().addHandler(logging.StreamHandler())


    logging.info('-----------------------')
    logging.info("           _     ")
    logging.info("        /\| |/\  ")
    logging.info("        \ ` ' /  ")
    logging.info("       |_     _| ")
    logging.info("        / , . \  ")
    logging.info("        \/|_|\/  ")
    logging.info('')
    logging.info('-----------------------')
         

    if shutil.which('pypher') == None:
        logging.info("pypher is required and must be in the path.")
        sys.exit()

    if shutil.which('fitstool.py') == None and template_fits == '':
        logging.info("If no template FITS is specified then owlcat's fitstool.py is required and must be in the path.")
        sys.exit()


    # Set up target beam
    if target_bmaj == '':
        logging.info('Please specify target beam size')
        sys.exit()
    else:
        target_bmaj = float(target_bmaj)/3600.0
    if target_bmin == '':
        target_bmin = target_bmaj
    else:
        target_bmin = float(options.target_bmin)/3600.0
    if target_bpa == '':
        target_bpa = 0.0
    else:
        target_bpa = float(options.target_bpa)


    # Set up residual image
    if residual_fits == '':
        if auto == 'wsclean':
            residual_fits = restored_fits.replace('image','residual')
        elif auto == 'ddfacet':
            residual_fits = restored_fits.replace('restored','residual')


    # Set up model image
    if model_fits == '':
        if auto == 'wsclean':
            model_fits = restored_fits.replace('image','model')
        elif auto == 'ddfacet':
            model_fits = restored_fits.replace('restored','model')


    # Set up output image
    if restored_conv_fits == '':
        restored_conv_fits = restored_fits.replace('.fits','.conv.fits')


    # Intermediate product names
    residual_conv_fits = residual_fits.replace('.fits','.conv.fits')
    model_conv_fits = model_fits.replace('.fits','.conv.fits')
    target_beam_fits = restored_fits.replace('.fits','_target_beam.fits')
    restoring_beam_fits = restored_fits.replace('.fits','.restoring-beam.fits')
    kernel_fits = restored_fits.replace('.fits','.kernel.fits')


    # Check for output files, create or steamroll them if overwrite = True
    outputs = [restored_conv_fits, residual_conv_fits, 
            model_conv_fits, target_beam_fits, restoring_beam_fits, kernel_fits]
    if all(list(map(os.path.isfile,outputs))) and not overwrite:
        logging.info("Found one or more existing output products and overwrite is set to False.")
        sys.exit()
    elif overwrite:
        if os.path.isfile(kernel_fits):
            # Special case to get around pypher's refusal to overwrite in all cases
            os.remove(kernel_fits)
        shutil.copyfile(restored_fits,residual_conv_fits)
        shutil.copyfile(restored_fits,restored_conv_fits)
        shutil.copyfile(restored_fits,model_conv_fits)
        if template_fits != '':
            shutil.copyfile(template_fits,target_beam_fits)
            shutil.copyfile(template_fits,restoring_beam_fits)
        else:
            os.system('fitstool.py -z '+str(cropsize)+' -o '+target_beam_fits+' '+restored_fits)
            os.system('fitstool.py -z '+str(cropsize)+' -o '+restoring_beam_fits+' '+restored_fits)
            drop_deg(target_beam_fits)
            drop_deg(restoring_beam_fits)


    logging.info('INPUTS')
    logging.info('Restored              : '+restored_fits)
    logging.info('Residual              : '+residual_fits)
    logging.info('Model                 : '+model_fits)
    logging.info('-----------------------')
    logging.info('OUTPUTS')
    logging.info('Restoring beam        : '+restoring_beam_fits)
    logging.info('Target beam           : '+target_beam_fits)
    logging.info('Homogenisation kernel : '+kernel_fits)
    logging.info('Model-conv            : '+model_conv_fits)
    logging.info('Residual-conv         : '+residual_conv_fits)
    logging.info('Restored-conv         : '+restored_conv_fits)
    logging.info('-----------------------')


    # Get the restoring beam
    bmaj,bmin,bpa,pixscale = get_header(restored_fits)
    logging.info('BEAMS')
    logging.info('Fitted bmaj           : '+str(bmaj*3600))
    logging.info('Fitted bmin           : '+str(bmin*3600))
    logging.info('Fitted bpa            : '+str(bpa))
    logging.info('Target bmaj           : '+str(target_bmaj*3600))
    logging.info('Target bmin           : '+str(target_bmin*3600))
    logging.info('Target bpa            : '+str(target_bpa))
    logging.info('-----------------------')


    # Render restoring beam image
    logging.info('Rendering restoring beam image...')
    xstd = bmin/(2.3548*pixscale)
    ystd = bmaj/(2.3548*pixscale)
    theta = deg2rad(bpa)
    restoring = Gaussian2DKernel(x_stddev=xstd,y_stddev=ystd,theta=theta,x_size=cropsize,y_size=cropsize,mode='center')
    restoring_beam_image = restoring.array
    restoring_beam_image = restoring_beam_image / numpy.max(restoring_beam_image)
    flush_fits(restoring_beam_image,restoring_beam_fits)


    # Render target beam image
    logging.info('Rendering target beam image...')
    target_xstd = target_bmin/(2.3548*pixscale)
    target_ystd = target_bmaj/(2.3548*pixscale)
    target_theta = deg2rad(target_bpa)
    target_gaussian = Gaussian2DKernel(x_stddev=target_xstd,y_stddev=target_ystd,theta=target_theta,x_size=cropsize,y_size=cropsize,mode='center')
    target_beam_image = target_gaussian.array
    target_beam_image = target_beam_image / numpy.max(target_beam_image)
    flush_fits(target_beam_image,target_beam_fits)


    # Call pypher to generate homogenisation kernel
    logging.info('Calling pypher to generate homogenisation kernel...')
    os.system('pypher '+restoring_beam_fits+' '+target_beam_fits+' '+kernel_fits)


    # Open model image and convolve with target beam
    logging.info('Convolving model image with target beam...')
    model_image = get_image(model_fits)
    model_conv_image = scipy.signal.fftconvolve(model_image, target_beam_image, mode='same')
    flush_fits(model_conv_image,model_conv_fits)


    # Open residual image and convolve with homogenisation kernel
    logging.info('Convolving residual image with homogenisation kernel...')
    residual_image = get_image(residual_fits)
    homogenisation_beam = get_image(kernel_fits)
    residual_conv_image = scipy.signal.fftconvolve(residual_image, homogenisation_beam, mode='same')
    flush_fits(residual_conv_image,residual_conv_fits)


    # Sum convolved model and residual
    logging.info('Summing convolved model and residual...')
    flush_fits(residual_conv_image+model_conv_image,restored_conv_fits)


    # Fix headers
    logging.info('Fixing headers...')
    beam_header(residual_conv_fits,target_bmaj,target_bmin,target_bpa)
    beam_header(model_conv_fits,target_bmaj,target_bmin,target_bpa)
    beam_header(restored_conv_fits,target_bmaj,target_bmin,target_bpa)


    # Clear up
    if clearup:
        logging.info('Clearing up...')
        to_remove = [residual_conv_fits, 
            model_conv_fits, target_beam_fits, restoring_beam_fits, kernel_fits]
        for ff in to_remove:
            os.remove(ff)


    logging.info('Done')
    logging.info('-----------------------')


















