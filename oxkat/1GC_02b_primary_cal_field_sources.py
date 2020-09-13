#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import glob
import os.path as o
import pickle
import subprocess
import sys
import tarfile
sys.path.append(o.abspath(o.join(o.dirname(sys.modules[__name__].__file__), "..")))


from oxkat import generate_jobs as gen
from oxkat import config as cfg


def main():


    DATA = cfg.DATA


    project_info = pickle.load(open('project_info.p','rb'), encoding = 'latin1')
    myms = project_info['master_ms']
    primary_id = project_info['primary_id']
    primary_name = project_info['primary_name']
    primary_tag = project_info['primary_tag']


    if cfg.CAL_1GC_PRIMARY_MODEL == 'auto':
        caltar = glob.glob(DATA+'/calmodels/*'+primary_tag+'*.tar.gz')
        if len(caltar) == 1:
            caltar = caltar[0]
            print('Found '+caltar+', untarring...')
            tf = tarfile.open(caltar)
            tf.extractall()
            fitslist = sorted(glob.glob(DATA+'/calmodels/*'+primary_tag+'*.fits'))
            nchan = len(fitslist)
            prefix = fitslist[0].split('-00')[-1]
            print('Prefix '+prefix+' has '+str(nchan)+' frequency planes')
        else:
            print('No model images found for '+primary_name)
    elif cfg.CAL_1GC_PRIMARY_MODEL == 'setjy':
        print('Component model for setjy requested, no additional image-based model prediction will be done.')
        prefix = ''
    else:
        prefix = cfg.CAL_1GC_PRIMARY_MODEL
        fitslist = sorted(glob.glob(prefix+'*.fits'))
        if len(fitslist) == 0:
            print('No FITS images found matching '+prefix+'*.fits')
            prefix = ''
        else:
            nchan = len(fitslist)
            print('Prefix '+prefix+' has '+str(nchan)+' frequency planes')

    if prefix != '':
        syscall = gen.generate_syscall_predict(msname=myms,imgbase=prefix,chanout=nchan)
        os.system(syscall)

if __name__ == "__main__":


    main()
