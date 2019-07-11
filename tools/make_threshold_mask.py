#!/usr/bin/env python
# ianh@astro.ox.ac.uk


from astropy.io import fits
from scipy.ndimage.morphology import binary_dilation
from shutil import copyfile
import numpy
import sys


def getImage(fitsfile):
	input_hdu = fits.open(fitsfile)[0]
	if len(input_hdu.data.shape) == 2:
	        image = numpy.array(input_hdu.data[:,:])
	elif len(input_hdu.data.shape) == 3:
	        image = numpy.array(input_hdu.data[0,:,:])
	else:
	        image = numpy.array(input_hdu.data[0,0,:,:])
	return image


def flushFits(newimage,fitsfile):
	f = fits.open(fitsfile,mode='update')
	input_hdu = f[0]
	if len(input_hdu.data.shape) == 2:
	        input_hdu.data[:,:] = newimage
	elif len(input_hdu.data.shape) == 3:
	        input_hdu.data[0,:,:] = newimage
	else:
	        input_hdu.data[0,0,:,:] = newimage
	f.flush()


def main():

	infits = sys.argv[1]
	thresh = float(sys.argv[2])

	opfits = infits.replace('.fits','_mask.fits')

	copyfile(infits,opfits)

	img = getImage(infits)
	maskimg = img * 0.0
	mask = img > thresh
	maskimg[mask] = 1.0

	maskimg = binary_dilation(maskimg)

	flushFits(maskimg,opfits)


if __name__ == "__main__":

    main()