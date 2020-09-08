#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import glob
import numpy
import os
import shutil
import sys
from astropy.io import fits
from optparse import OptionParser



def getImage(fitsfile):
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

def flushFits(newimage,fitsfile):
        f = fits.open(fitsfile,mode='update')
        input_hdu = f[0]
        if len(input_hdu.data.shape) == 2:
                input_hdu.data[:,:] = newimage
        elif len(input_hdu.data.shape) == 3:
                input_hdu.data[0,:,:] = newimage
        elif len(input_hdu.data.shape) == 4:
                input_hdu.data[0,0,:,:] = newimage
        else:
                input_hdu.data[0,0,0,:,:] = newimage
        f.flush()



def main():

    parser = OptionParser(usage = '%prog [options]')
    parser.add_option('--pbfits', dest = 'pbfits', help = 'Primary beam FITS image')
    parser.add_option('--pattern', dest = 'pattern', help = 'Pattern for images to correct')
    parser.add_option('--threshold', dest = 'threshold', help = 'Primary beam cutoff (default = 0.3)', default = 0.3)
    parser.add_option('--doweight', dest = 'doweight', help = 'Save a weight image for mosaicking', action = 'store_true', default = False)

    (options,args) = parser.parse_args()
    pbfits = options.pbfits
    pattern = options.pattern
    threshold = float(options.threshold)
    doweight = options.doweight

    pbimg = getImage(pbfits)
    mask = pbimg < threshold
    pbimg[mask] = numpy.nan

    fitslist = glob.glob(pattern)

    for infits in fitslist:
        
        pbcorfits = infits.replace('.fits','_pbcor.fits')

        if os.path.isfile(pbcorfits):
            print(pbcorfits,'exists, skipping')
        else:
            print('Correcting',infits)
            shutil.copy(infits,pbcorfits)
            inimg = getImage(infits)
            pbcorimg = inimg / pbimg
            flushFits(pbcorimg,pbcorfits)
            if doweight:
                wtfits = infits.replace('.fits','_wt.fits')
                shutil.copy(infits,wtfits)
                flushFits(pbimg**2.0,wtfits)


if __name__ == "__main__":


    main()
