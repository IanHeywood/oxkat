#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


# Clip killMS solutions based on the first differential of the amplitudes


import numpy
import sys


def nan_helper(y):
	# https://stackoverflow.com/questions/6518811/interpolate-nan-values-in-a-numpy-array    
    return numpy.isnan(y), lambda z: z.nonzero()[0]


gaintab = sys.argv[1]
optab = gaintab.replace('.npz','_scrubbed.npz')
thresh = 5.0


tab = dict(numpy.load(gaintab))


clusters = tab['ClusterCat']
freqs = tab['FreqDomains']
ant_names = tab['StationNames']
t0 = tab['Sols']['t0']
t1 = tab['Sols']['t1']
dt = t1 - t0
t = t0 + (dt/2)


gains = (tab['Sols'])
gains = gains.view(numpy.recarray)


gshape = gains['G'].shape
nt = gshape[0]
nfreq = gshape[1]
nant = gshape[2]
ndir = gshape[3]
ncorr1 = gshape[4]
ncorr2 = gshape[5]


print (gaintab,'properties:')
print ('')
print ('Time slots:       '+str(nt))
print ('Frequency chunks: '+str(nfreq))
print ('Antennas:         '+str(nant))
print ('Directions:       '+str(ndir))
print ('Correlations:     '+str(ncorr1*ncorr2))


for ant in range(0,nant):

	for mydir in range(0,ndir):

		for corr1,corr2 in [(0,0),(1,1)]:

			g0 = (gains['G'][:,0,ant,mydir,corr1,corr2])

			amp = numpy.abs(g0)
			phase = numpy.angle(g0)

			fd = numpy.gradient(amp)
			fd_mean = numpy.mean(fd)
			fd_std = numpy.std(fd)

			mask = abs(fd) > 0.1

			amp[mask] = numpy.nan

			nans, x= nan_helper(amp)
			amp[nans]= numpy.interp(x(nans), x(~nans), amp[~nans])

			g1 = amp * numpy.exp(1j*phase)

			gains['G'][:,0,ant,mydir,corr1,corr2] = g1


tab['Sols'] = gains
numpy.savez(optab,**tab)

