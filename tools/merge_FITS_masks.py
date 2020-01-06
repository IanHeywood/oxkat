#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


from astropy.io import fits
import numpy
import random
from scipy.ndimage.morphology import binary_dilation
import shutil
import sys


def genhex():
    ran = random.randrange(10**80)
    myhex = "%064x" % ran
    myhex = myhex[:32]
    return myhex


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

    prefix = sys.argv[1]
    opfits = sys.argv[2]

    modelfits = prefix+'-MFS-model.fits'
    makemaskfits = prefix+'-MFS-image.fits.mask.fits'

    shutil.copyfile(modelfits,opfits)

    modeldata = getImage(modelfits)
    makemaskdata = getImage(makemaskfits)

    finalmaskdata = modeldata+makemaskdata

    finalmaskdata = binary_dilation(finalmaskdata,iterations=4)

    flushFits(finalmaskdata,opfits)



if __name__ == "__main__":


    main()
