#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import imageio
import numpy
from argparse import ArgumentParser
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


def fft_image(image):
    fft_image = numpy.fft.fftshift(numpy.fft.fft2(image))
    amplitudes = numpy.abs(fft_image)
    return amplitudes


def hist_eq(image,nbins):
    hist,bins = numpy.histogram(image.flatten(), nbins, density = True)
    cdf = hist.cumsum()
    cdf = nbins * cdf / cdf[-1]
    image_eq = numpy.interp(image.flatten(), bins[:-1], cdf)
    image_eq = image_eq.reshape(image.shape)
    return image_eq


def main():

    parser = ArgumentParser(description='FFT a FITS images and render the amplitudes to a PNG for inspection')

    parser.add_argument('infits', 
                      help = 'Input FITS image')
    parser.add_argument('-o','--output', dest = 'pngname',
                      help = 'Output PNG name (default is based on input FITS name)', default = '')
    parser.add_argument('--noeq', dest = 'noeq',
                      help = 'Disable histogram equalisation', default = False, action = 'store_true')
    parser.add_argument('-n','--nbins', dest = 'nbins',
                      help = 'Number of bins for histogram equalisation (default = 1024)', default = 1024)

    options = parser.parse_args()
    infits = options.infits
    pngname =  options.pngname
    noeq = options.noeq
    nbins = int(options.nbins)


    img = get_image(infits)
    fftimg = fft_image(img)

    if not noeq:
        fftimg = hist_eq(fftimg,nbins)

    if pngname == '':
        pngname = infits+'_FFT_amplitudes.png'

    imageio.imwrite(pngname,fftimg)


if __name__ == "__main__":


    main()
