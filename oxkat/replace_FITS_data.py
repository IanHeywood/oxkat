#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


from astropy.io import fits
import random
import shutil
import sys


def genhex()
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

    headerfits = sys.argv[1]

    datafits = sys.argv[2]

    tempfits = genhex()+'.fits'

    shutil.copyfile(headerfits,tempfits)

    imgdata = getImage(datafits)

    flushFits(imgdata,tempfits)

    shutil.move(tempfits,datafits)



if __name__ == "__main__":


    main()
