import numpy
import sys
from astropy.io import fits
from scipy.ndimage.morphology import binary_dilation


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


infits = sys.argv[1]
niter = int(sys.argv[2])

maskimage = getImage(infits)
dilated = binary_dilation(input=maskimage,iterations=niter)
flushFits(dilated,infits)