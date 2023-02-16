#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import glob
import numpy
import shutil
from astropy import wcs
from astropy.io import fits
from optparse import OptionParser


# ---------------------------------------------------------------------------------------


def hms2deg(hms,delimiter=':'):

    """ 
    Right ascention string in hms to float in decimal degrees
    """

    h,m,s = hms.split(delimiter)
    h = float(h)
    m = float(m)
    s = float(s)
    deg = 15.0*(h+(m/60.0)+(s/3600.0))
    return deg


def dms2deg(dms,delimiter=':'):

    """
    Declination string in dms to float in decimal degrees
    """

    d,m,s = dms.split(delimiter)
    if d[0] == '-':
        decsign = -1.0
        d = float(d[1:])
    elif d[0] == '+':
        decsign = 1.0
        d = float(d[1:])
    else:
        decsign = 1.0
        d = float(d)
    m = float(m)
    s = float(s)
    deg = decsign*(d+(m/60.0)+(s/3600.0))

    return deg


def radius2deg(radius):

    """
    String with arcsec or arcmin unit to decimal degrees
    """

    if radius[-1] == '"':
        radius = float(radius[:-1])/3600.0
    elif radius[-1] == "'":
        radius = float(radius[:-1])/60.0
    else:
        radius = float(radius)

    return radius


def process_region_file(region_file):

    """
    Extract RA,dec,radius as floats in degrees
    from a DS9 region file containing circles
    """

    circles = []

    f = open(region_file,'r')
    line = f.readline()
    while line:
        if line[0:6] == 'circle':
            line = line.replace(' ','')
            line = line.rstrip('\n').replace('(',' ').replace(')',' ')
            ra,dec,radius = line.split()[1].split(',')
            if ':' in  ra:
                ra = hms2deg(ra)
            else:
                ra = float(ra)
            if ':' in dec:
                dec = dms2deg(dec)
            else:
                dec = float(dec)
            radius = radius2deg(radius)
            circles.append((ra,dec,radius))
        line = f.readline()
    f.close()

    return circles


def get_image(fits_file):

    """
    Get the image data from a FITS file
    """

    input_hdu = fits.open(fits_file)[0]
    if len(input_hdu.data.shape) == 2:
        image = numpy.array(input_hdu.data[:,:])
    elif len(input_hdu.data.shape) == 3:
        image = numpy.array(input_hdu.data[0,:,:])
    else:
        image = numpy.array(input_hdu.data[0,0,:,:])

    return image


def flush_fits(image,fits_file):

    """
    Write 2D numpy array image to fits_file
    """

    f = fits.open(fits_file,mode='update')
    input_hdu = f[0]
    if len(input_hdu.data.shape) == 2:
        input_hdu.data[:,:] =image
    elif len(input_hdu.data.shape) == 3:
        input_hdu.data[0,:,:] = image
    else:
        input_hdu.data[0,0,:,:] = image
    f.flush()


def apply_circle(image,xpix,ypix,rpix):

    """
    Apply a circle with values of 1, of radius rpix to xpix,ypix in image array
    """

    xg,yg = numpy.mgrid[int(xpix-rpix):int(xpix+rpix)+1,int(ypix-rpix):int(ypix+rpix)+1]
    xg = xg.ravel()
    yg = yg.ravel()

    for i,j in zip(xg,yg):
        sep = ((i-xpix)**2.0 + (j-ypix)**2.0)**0.5
        if sep < rpix:
            image[j,i] = 1.0

    return image


def fmt(xx):
    return str(round(xx,5))


def spacer():
    print('--------------|---------------------------------------------')


# ---------------------------------------------------------------------------------------


def main():

    parser = OptionParser(usage = '%prog [options]')
    parser.add_option('--region', dest = 'region_file', help = 'DS9 region file')
    parser.add_option('--prefix', dest = 'model_pattern', help = 'wsclean image prefix')
    parser.add_option('--subtract', dest = 'subtract', help = 'Produce model image with components within region subtracted (default = False)', action = 'store_true', default = False)
    (options,args) = parser.parse_args()
    region_file = options.region_file
    model_pattern = options.model_pattern
    subtract = options.subtract

    circles = process_region_file(region_file)
    suffix = region_file.split('/')[-1].split('.')[0]

    spacer()
    print('DS9 region    : '+region_file)
    print('Contains      : '+str(len(circles))+' circles')
    print('Model suffix  : '+suffix)
    spacer()

    model_list = sorted(glob.glob(model_pattern+'-0*model*fits'))

    for fits_file in model_list:

        print('Reading       : '+fits_file)

        dir1_fits = fits_file.replace(model_pattern,model_pattern+'-'+suffix)

        if subtract:
            subtract_fits = fits_file.replace(model_pattern,model_pattern+'-'+suffix+'-subtracted')

        img = get_image(fits_file)
        mask = img*0.0

        hdulist = fits.open(fits_file)
        w = wcs.WCS(hdulist[0].header)
        ref_pix1 = hdulist[0].header['CRPIX1']
        ref_pix2 = hdulist[0].header['CRPIX2']
        pixscale = hdulist[0].header['CDELT2']

        for circle in circles:
            ra = circle[0]
            dec = circle[1]
            coord = (ra,dec,0,0)
            pixels = w.wcs_world2pix([coord],0)
            radius = circle[2]
            xpix = pixels[0][0]
            ypix = pixels[0][1]
            rpix = radius/pixscale
            print('Masking       : sky '+fmt(ra)+' '+fmt(dec)+' '+fmt(radius))
            print('              : pixel '+fmt(xpix)+' '+fmt(ypix)+' '+fmt(rpix))
            mask = apply_circle(mask,xpix,ypix,rpix)

        dir1 = img*mask

        print('Writing       : '+dir1_fits)
        shutil.copyfile(fits_file,dir1_fits)
        flush_fits(dir1,dir1_fits)

        if subtract:
            subt = img*(1.0-mask)
            print('Writing       : '+subtract_fits)
            shutil.copyfile(fits_file,subtract_fits)
            flush_fits(subt,subtract_fits)


        spacer()


if __name__ == '__main__':

    main()
