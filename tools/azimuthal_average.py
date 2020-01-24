#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


# Requires: pip install scikit-ued


import numpy
import shutil
import sys
from astropy.io import fits
from skued import azimuthal_average as aa


def getImage(fitsfile):
        input_hdu = fits.open(fitsfile)[0]
        if len(input_hdu.data.shape) == 2:
                image = numpy.array(input_hdu.data[:,:])
        elif len(input_hdu.data.shape) == 3:
                image = numpy.array(input_hdu.data[0,:,:])
        elif len(input_hdu.data.shape) == 4:
                image = numpy.array(input_hdu.data[0,0,:,:])
        elif len(input_hdu.data.shape) == 5:
                image = numpy.array(input_hdu.data[0,0,0,:,:])
        return image


def flushFits(newimage,fitsfile):
        f = fits.open(fitsfile,mode='update')
        input_hdu = f[0]
        if len(input_hdu.data.shape) == 2:
                input_hdu.data[:,:] = newimage
        elif len(input_hdu.data.shape) == 3:
                input_hdu.data[0,:,:] = newimage
        elif len(input_hdu.data.shape) == 4:
                input_hdu.data[0,0,:,:] = newimage
        elif len(input_hdu.data.shape) == 5:
                input_hdu.data[0,0,0,:,:] = newimage
        f.flush()


def main():

        input_fits = sys.argv[1]

        output_fits = input_fits.replace('.fits','_azavg.fits')

        shutil.copyfile(input_fits,output_fits)

        input_img = getImage(input_fits)
        output_img = input_img * 0.0
        ny,nx = input_img.shape
        x0 = int(nx/2)
        y0 = int(ny/2)

        radius,average = aa(input_img,center=(x0,y0))

        for y in range(0,ny):
        	for x in range(0,nx):
        		val = (((float(y)-y0)**2.0)+((float(x)-x0)**2.0))**0.5
        		output_img[y][x] = average[int(val)]

        flushFits(output_img,output_fits)



if __name__ == "__main__":


    main()