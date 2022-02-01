import numpy
import shutil
import sys
from astropy.io import fits


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


im1 = sys.argv[1]
operator = sys.argv[2].upper()
im2 = sys.argv[3]
out = sys.argv[4]

shutil.copyfile(im1,out)

data1 = getImage(im1)
data2 = getImage(im2)

if operator == 'OR':
	dataout = numpy.logical_or(data1,data2)
elif operator == 'AND':
	dataout = numpy.logical_and(data1,data2)
elif operator == 'XOR':
	dataout = numpy.logical_xor(data1,data2)
else:
	print('Operator not recognised, please use OR, AND or XOR')
	sys.exit()

flushFits(dataout,out)
