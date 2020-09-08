#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk

# Convert a DS9 (circles only) region file to a ClusterCat.npy file
# for use with killMS. This is a pure Python script to avoid having
# to invoke MakeModel.py for this simple purpose.


import numpy
import sys
from optparse import OptionParser


def deg2rad(xx):
    return xx*numpy.pi/180.0

def hms2deg(ra,delimiter=':'):
    hms = numpy.fromstring(ra,dtype='float',sep=delimiter)
    radeg = 15.0*((hms[0])+(hms[1]/60.0)+(hms[2]/3600.0))
    return radeg

def dms2deg(dec,delimiter=':'):
    if dec[0] == '+':
        sign = 1.0
        dec = dec.lstrip('+')
    elif dec[0] == '-':
        sign = -1.0
        dec = dec.lstrip('-')
    else:
        sign = 1.0
    dms = numpy.fromstring(dec,dtype='float',sep=delimiter)
    dec = sign * ((dms[0])+(dms[1]/60.0)+(dms[2]/3600.0))
    return dec


def main():

    parser = OptionParser(usage = '%prog [options] regionfile')
    parser.add_option('--outname', dest = 'outname', default = '', help = 'Name of output npy file (default = append .npy)')
    (options,args) = parser.parse_args()
    outname = options.outname


    if len(args) != 1:
        print('Please specify a DS9 region file')
        sys.exit()
    else:
        regfile = args[0]

    if outname == '':
        npyfile = regfile+'.npy'
    else:
        npyfile = outname


    print('Reading '+regfile)

    centres = []
    f = open(regfile,'r')
    line = f.readline()
    while line:
        if line[0:6] == 'circle':
            coords = line.split('(')[-1].split(')')[0]
            x,y,rad = coords.split(',')
            ra = hms2deg(x)
            dec = dms2deg(y)
            centres.append((ra,dec))
        line = f.readline()
    f.close()


    ClusterCat=numpy.zeros((len(centres),),dtype=[('Name','|S200'),('ra',numpy.float),('dec',numpy.float),('SumI',numpy.float),("Cluster",int)])


    for i in range(0,len(centres)):
        ClusterCat[i]['Name'] = str(i)
        ClusterCat[i]['ra'] = deg2rad(centres[i][0])
        ClusterCat[i]['dec'] = deg2rad(centres[i][1])
        ClusterCat[i]['SumI'] = 1.0
        ClusterCat[i]['Cluster'] = i

    print('Writing '+npyfile)

    numpy.save(npyfile,ClusterCat)



if __name__ == '__main__':

    main()