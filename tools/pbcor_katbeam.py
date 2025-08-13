#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


# Requires:
# https://github.com/ludwigschwardt/katbeam
# https://pypi.org/project/scikit-ued/


import numpy as np
import os
import sys
import time
from astropy.io import fits
from katbeam import JimBeam
from optparse import OptionParser
from shutil import copyfile



def msg(txt):
    stamp = time.strftime(' %Y-%m-%d %H:%M:%S | ')
    print(stamp+txt)


def check_file(filename):
    exists = False
    if os.path.isfile(filename):
        msg(filename+' exists, will not overwrite')
        exists = True
    return exists


def check_name(name1,name2):
    if name1 == name2:
        msg('Problem with auto-generated output name (does your input file have a .fits suffix?)')
        sys.exit()


def get_header(fitsfile,freqaxis):
    inphdu = fits.open(fitsfile)
    inphdr = inphdu[0].header
    nx = inphdr.get('NAXIS1')
    ny = inphdr.get('NAXIS2')
    dx = inphdr.get('CDELT1')
    dy = inphdr.get('CDELT2')
    freq = inphdr.get('CRVAL'+freqaxis)
    return nx,ny,dx,dy,freq


def get_image(fitsfile):
    input_hdu = fits.open(fitsfile)[0]
    if len(input_hdu.data.shape) == 2:
            image = np.array(input_hdu.data[:,:])
    elif len(input_hdu.data.shape) == 3:
            image = np.array(input_hdu.data[0,:,:])
    else:
            image = np.array(input_hdu.data[0,0,:,:])
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



def main():


    # -------------------------------------------------
    # Options and some error checking

    parser = OptionParser(usage = '%prog [options] input_fits')
    parser.add_option('--band', dest = 'band', help = 'Select [U]HF or [L]-band (default = L-band)', default = 'L')
    parser.add_option('--freq', dest = 'freq', help = 'Frequency in MHz at which to evaluate beam model (default = get from input FITS header)', default = '')
    parser.add_option('--freqaxis', dest = 'freqaxis', help = 'Frequency axis in FITS header (default = 3, set to 4 for DDFacet images)', default = '3')
    parser.add_option('--pbcut', dest = 'pbcut', help = 'Primary beam gain level beyond which to blank output images (default = 0.3)', default = 0.3)
    parser.add_option('--noavg', dest = 'azavg', help = 'Do not azimuthally-average the primary beam pattern (default = do this)', default = True, action = 'store_false')
    parser.add_option('--nopbcorfits', dest = 'savepbcor', help = 'Do not save primary beam corrected image (default = save corrected image)', action = 'store_false', default = True)
    parser.add_option('--nopbfits', dest = 'savepb', help = 'Do not save primary beam image (default = save PB image)', action = 'store_false', default = True)
    parser.add_option('--nowtfits', dest = 'savewt', help = 'Do not save weight image (default = save weight image)', action = 'store_false', default = True)
    parser.add_option('--pbcorname', dest = 'pbcor_fits', help = 'Filename for primary beam corrected image (default = based on input image)', default = '')
    parser.add_option('--pbname', dest = 'pb_fits', help = 'Filename for primary beam image (default = based on input image)', default = '')
    parser.add_option('--wtname', dest = 'wt_fits', help = 'Filename for weight image (default = based on input image)', default = '')
    parser.add_option('--overwrite', '-f', dest = 'overwrite', help = 'Overwrite any existing output files (default = do not overwrite)', action = 'store_true', default = False)
    (options,args) = parser.parse_args()

    # Input FITS file
    if len(args) != 1:
        msg('Please provide a FITS image')
        sys.exit()
    else:
        input_fits = args[0].rstrip('/')

    # MeerKAT band
    band = options.band[0].lower()
    if band not in ['l','u','s']:
        msg('Please check requested band')
        sys.exit()

    # Frequency
    freq = options.freq
    freqaxis = options.freqaxis

    # Primary beam cut level
    pbcut = float(options.pbcut)

    # Azimuthal averaging
    azavg = options.azavg
    if azavg:
        try:
            from skued import azimuthal_average as aa
        except:
            msg('scikit-ued not found, azimuthal averaging is not available.')
            msg('Try: pip install scikit-ued')
            azavg = False

    # Output files
    savepbcor = options.savepbcor
    savepb = options.savepb
    savewt = options.savewt
    if [savepbcor,savepb,savewt] == [False,False,False]:
        msg('Nothing to do, please check your options')
        sys.exit()

    # Generate output names if not provided
    pbcor_fits = options.pbcor_fits
    pb_fits = options.pb_fits
    wt_fits = options.wt_fits

    if pbcor_fits == '':
        pbcor_fits = input_fits.replace('.fits','.pbcor.fits')
        check_name(input_fits,pbcor_fits)
    if pb_fits == '':
        pb_fits = input_fits.replace('.fits','.pb.fits')
        check_name(input_fits,pb_fits)
    if wt_fits == '':
        wt_fits = input_fits.replace('.fits','.wt.fits')
        check_name(input_fits,wt_fits)

    # Bail out if some files will be overwritten
    overwrite = options.overwrite
    if not overwrite:
        file_check = []
        if savepbcor:
            file_check.append(check_file(pbcor_fits))
        if savepb:
            file_check.append(check_file(pb_fits))
        if savewt:
            file_check.append(check_file(wt_fits))
        if True in file_check:
            sys.exit()  

    pol = 'I' # hardwired Stokes I beam for now

    # -------------------------------------------------

    # Set up band
    if band == 'l':
        beam_model = 'MKAT-AA-L-JIM-2020'
        band = 'L-band'
    elif band == 'u':
        beam_model = 'MKAT-AA-UHF-JIM-2020'
        band = 'UHF'
    elif band == 's':
        beam_model = 'MKAT-AA-S-JIM-2020'
        band = 'S-band' 
    msg('Band is '+band)
    msg('Beam model is '+beam_model)
    beam = JimBeam(beam_model)

    # Get header info
    msg('Reading FITS image')
    msg(' <--- '+input_fits)
    nx,ny,dx,dy,fitsfreq = get_header(input_fits,freqaxis)
    if nx != ny or abs(dx) != abs(dy):
        msg('Can only handle square images / pixels')
        sys.exit()
    extent = nx*dx # degrees

    if freq == '':
        freq = fitsfreq/1e6
    else:
        freq = float(freq)

    msg('Evaluating beam at '+str(round(freq,4))+' MHz')
    interval = np.linspace(-extent/2.0,extent/2.0,nx)
    xx,yy = np.meshgrid(interval,interval)
    beam_image = beam.I(xx,yy,freq)

    msg('Masking beam beyond the '+str(pbcut)+' level')
    mask = beam_image < pbcut
    beam_image[mask] = np.nan

    if azavg:
        msg('Azimuthally averaging the beam pattern')
        ny, nx = beam_image.shape
        x0, y0 = nx // 2, ny // 2
        radius, average = aa(beam_image, center=(x0, y0)) 
        yy, xx = np.ogrid[:ny, :nx]
        r = np.hypot(yy - y0, xx - x0)          
        idx = np.clip(r.astype(np.int32), 0, len(average) - 1)
        beam_image[...] = average[idx]      

        # x0 = int(nx/2)
        # y0 = int(ny/2)
        # radius,average = aa(beam_image,center=(x0,y0))
        # # This can probably be sped up...
        # for y in range(0,ny):
        #     for x in range(0,nx):
        #         val = (((float(y)-y0)**2.0)+((float(x)-x0)**2.0))**0.5
        #         beam_image[y][x] = average[int(val)]

    if savepbcor:
        msg('Correcting image')
        input_image = get_image(input_fits)
        pbcor_image = input_image / beam_image
        msg('Writing primary beam corrected image')
        msg(' ---> '+pbcor_fits)
        copyfile(input_fits,pbcor_fits)
        flush_fits(pbcor_image,pbcor_fits)
    if savepb:
        msg('Writing primary beam image')
        msg(' ---> '+pb_fits)
        copyfile(input_fits,pb_fits)
        flush_fits(beam_image,pb_fits)
    if savewt:
        msg('Writing weight (pb^2) image')
        msg(' ---> '+wt_fits)
        copyfile(input_fits,wt_fits)
        flush_fits(beam_image**2.0,wt_fits)

    msg('Done')


if __name__ == "__main__":

    main()
