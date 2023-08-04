import sys
import glob
import numpy
from astropy.io import fits


def get_image(fitsfile):
    input_hdu = fits.open(fitsfile)[0]
    if len(input_hdu.data.shape) == 2:
            image = numpy.array(input_hdu.data[:,:])
    elif len(input_hdu.data.shape) == 3:
            image = numpy.array(input_hdu.data[0,:,:])
    else:
            image = numpy.array(input_hdu.data[0,0,:,:])
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


pattern = sys.argv[1]


fitslist = sorted(glob.glob(pattern+'*model.fits'))
for fitsfile in fitslist:
        img = get_image(fitsfile)
        maxval = numpy.max(img)
        if numpy.isnan(maxval):
                new_img = numpy.zeros((img.shape[0],img.shape[1]))
                print(fitsfile,maxval,'zeroing NaN model')
                flush_fits(new_img,fitsfile)
        else:
                print(fitsfile,maxval)