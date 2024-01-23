#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import logging
import numpy
import shutil
import sys
from astropy.io import fits
from datetime import datetime
from optparse import OptionParser


def get_image(fitsfile):
    input_hdu = fits.open(fitsfile)[0]
    if len(input_hdu.data.shape) == 2:
            image = numpy.array(input_hdu.data[:,:])
    elif len(input_hdu.data.shape) == 3:
            image = numpy.array(input_hdu.data[0,:,:])
    else:
            image = numpy.array(input_hdu.data[0,0,:,:])
    return image


def flush_fits(image,fits_file):
    f = fits.open(fits_file,mode='update')
    input_hdu = f[0]
    if len(input_hdu.data.shape) == 2:
        input_hdu.data[:,:] =image
    elif len(input_hdu.data.shape) == 3:
        input_hdu.data[0,:,:] = image
    else:
        input_hdu.data[0,0,:,:] = image
    f.flush()


def exist(ff):
    exist = os.path.isfile(ff)
    return


def linearpol(qimg,uimg):
    limg = numpy.sqrt((qimg**2)+(uimg**2))
    return limg


def totalpol(qimg,uimg,vimg):
    pimg = numpy.sqrt((qimg**2)+(uimg**2)+(vimg**2))
    return pimg


def pa(qimg,uimg):
    paimg = numpy.degrees(0.5*numpy.arctan(uimg/qimg))
    return paimg


date_time = datetime.now()
timestamp = date_time.strftime('%d%m%Y_%H%M%S')
logfile = 'polfits_'+timestamp+'.log'
logging.basicConfig(filename=logfile, level=logging.DEBUG, format='%(asctime)s: %(message)s', datefmt='%d/%m/%Y %H:%M:%S ',force=True)
logging.getLogger().addHandler(logging.StreamHandler())


def main():

    parser = OptionParser(usage = '%prog [options] Ifits')
    parser.add_option('--threshold', dest = 'threshold', help = 'Total intensity threshold below which fractional products are masked (default 1 mJy)',default = 1e-3)
    parser.add_option('--no-total', dest = 'dototal', help = 'Do not create total polarised intensity image', action = 'store_false', default = True)
    parser.add_option('--no-linear', dest = 'dolinear', help = 'Do not create linear polarised intensity image', action = 'store_false', default = True)
    parser.add_option('--no-angle', dest = 'doangle', help = 'Do not create polarised angle image', action = 'store_false', default = True)
    parser.add_option('--no-frac', dest = 'dofrac', help = 'Do not create fractional polarised intensity images', action = 'store_false', default = True)
    parser.add_option('--writemask', dest = 'writemask', help = 'Write out the mask as a FITS file', action = 'store_true', default = False)

    (options,args) = parser.parse_args()
    threshold = float(options.threshold)
    dototal = options.dototal
    dolinear = options.dolinear
    doangle = options.doangle
    dofrac = options.dofrac
    writemask = options.writemask

    if len(args) != 1:
        logging.error('Please specify a Stokes I image')
        sys.exit()

    ifits = args[0]
    qfits = ifits.replace('-I-','-Q-')
    ufits = ifits.replace('-I-','-U-')
    vfits = ifits.replace('-I-','-V-')

    lfits = ifits.replace('-I-','-linear-')
    pfits = ifits.replace('-I-','-totalpol-')
    pafits = ifits.replace('-I-','-pa-')
    lfracfits = ifits.replace('-I-','-linearfrac-')
    cfracfits = ifits.replace('-I-','-circfrac-')

    logging.info(f'Reading {ifits}')
    iimg = get_image(ifits)
    logging.info(f'Reading {qfits}')
    qimg = get_image(qfits)
    logging.info(f'Reading {ufits}')
    uimg = get_image(ufits)
    logging.info(f'Reading {vfits}')
    vimg = get_image(vfits)

    maskimg = iimg > threshold
    out_products = []

    if dolinear:
        logging.info('Forming linear polarisation image')
        limg = linearpol(qimg,uimg)
        out_products.append((limg,lfits))
    if dototal:
        logging.info('Forming total polarisation image')
        pimg = totalpol(qimg,uimg,vimg)
        out_products.append((pimg,pfits))
    if doangle:
        logging.info('Forming polarisation angle image')
        paimg = pa(qimg,uimg)
        out_products.append((paimg,pafits))
    if dofrac:
        logging.info('Forming fractional linear polarisation image')
        lfracimg = limg/iimg
        lfracimg[~maskimg] = numpy.nan
        out_products.append((lfracimg,lfracfits))
        logging.info('Forming fractional circular polarisation image')
        cfracimg = numpy.abs(vimg)/iimg
        cfracimg[~maskimg] = numpy.nan
        out_products.append((cfracimg,cfracfits))

    for op in out_products:
        opimg = op[0]
        opfits = op[1]
        logging.info(f'Writing {opfits}')
        shutil.copyfile(ifits,opfits)
        flush_fits(opimg,opfits)
    
    logging.info('Done')


if __name__ == '__main__':

    main()


