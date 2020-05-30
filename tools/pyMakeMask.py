import numpy
import scipy.ndimage
import scipy.special
import shutil
from astropy.io import fits
from optparse import OptionParser
from scipy.ndimage.morphology import binary_dilation


def get_image(fitsfile):
    print('Reading '+fitsfile)
    input_hdu = fits.open(fitsfile)[0]
    if len(input_hdu.data.shape) == 2:
            image = numpy.array(input_hdu.data[:,:])
    elif len(input_hdu.data.shape) == 3:
            image = numpy.array(input_hdu.data[0,:,:])
    else:
            image = numpy.array(input_hdu.data[0,0,:,:])
    return image


def flush_fits(newimage,fitsfile):
    print('Writing '+fitsfile)
    f = fits.open(fitsfile,mode='update')
    input_hdu = f[0]
    if len(input_hdu.data.shape) == 2:
            input_hdu.data[:,:] = newimage
    elif len(input_hdu.data.shape) == 3:
            input_hdu.data[0,:,:] = newimage
    else:
            input_hdu.data[0,0,:,:] = newimage
    f.flush()


def make_noise_map(restored_image,boxsize):
    # Cyril's magic minimum filter
    # Plundered from the depths of https://github.com/cyriltasse/DDFacet/blob/master/SkyModel/MakeMask.py
    print('Generating noise map')
    box = (boxsize,boxsize)
    n = boxsize**2.0
    x = numpy.linspace(-10,10,1000)
    f = 0.5 * (1.0 + scipy.special.erf(x / numpy.sqrt(2.0)))
    F = 1.0 - (1.0 - f)**n
    ratio = numpy.abs(numpy.interp(0.5, F, x))
    noise = -scipy.ndimage.filters.minimum_filter(restored_image, box) / ratio
    negative_mask = noise < 0.0
    noise[negative_mask] = 1.0e-10
    median_noise = numpy.median(noise)
    median_mask = noise < median_noise
    noise[median_mask] = median_noise
    print('Median noise value is '+str(median_noise))
    return noise


def main():

    parser = OptionParser(usage = '%prog [options] restored_image')
    parser.add_option('--threshold', dest = 'threshold', help = 'Sigma threshold for masking (default = 6.5)', default = 6.5)
    parser.add_option('--boxsize', dest = 'boxsize', help = 'Box size over which to compute stats (default = 50)', default = 50)
    parser.add_option('--dilate', dest = 'dilate', help = 'Number of iterations of binary dilation (default = 0)', default = 0)
    parser.add_option('--savenoise', dest = 'savenoise', help = 'Enable to export noise image as FITS file (default = do not save noise image', action = 'store_true', default = False)
    parser.add_option('--outfile', dest = 'outfile', help = 'Suffix for mask image (default = restored_image.replace(".fits",".mask.fits"))', default = '')
    (options,args) = parser.parse_args()
    threshold = float(options.threshold)
    boxsize = int(options.boxsize)
    dilate = int(options.dilate)
    savenoise = options.savenoise
    outfile = options.outfile

    if len(args) != 1:
        print('Please specify a FITS file')
        sys.exit()
    else:
        input_fits = args[0].rstrip('/')

    input_image = get_image(input_fits)

    noise_image = make_noise_map(input_image, boxsize)
    if savenoise:
        noise_fits = input_fits.replace('.fits', '.noise.fits')
        shutil.copyfile(input_fits, noise_fits)
        flush_fits(noise_image, noise_fits)

    mask_image = input_image > threshold * noise_image

    mask_image[:,-1]=0
    mask_image[:,0]=0
    mask_image[0,:]=0
    mask_image[-1,:]=0

    if dilate != 0:
        print('Dilating mask, '+str(dilate)+' iteration(s)')
        dilated = binary_dilation(input = mask_image, iterations = dilate)
        mask_image = dilated

    if outfile == '':
        mask_fits = input_fits.replace('.fits', '.mask.fits')
    else:
        mask_fits = outfile
    shutil.copyfile(input_fits, mask_fits)

    flush_fits(mask_image,mask_fits)

    print('Done')


if __name__ == '__main__':
    main()

