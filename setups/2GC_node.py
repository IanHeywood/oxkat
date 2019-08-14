#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import os.path as o
import pickle
import sys
sys.path.append(o.abspath(o.join(o.dirname(sys.modules[__name__].__file__), "..")))


from oxkat import generate_jobs as gen


def main():
    
    
    CWD = gen.CWD
    OXKAT = gen.OXKAT
    PARSETS = gen.PARSETS
    SCRIPTS = gen.SCRIPTS
    LOGS = gen.LOGS
    WSCLEAN_CONTAINER = gen.XWSCLEAN_CONTAINER
    CUBICAL_CONTAINER = gen.XCUBICAL_CONTAINER
    DDFACET_CONTAINER = gen.XDDFACET_CONTAINER 


    submit_file = 'run_2GC_jobs.sh'


    gen.setup_dir(SCRIPTS)
    gen.setup_dir(LOGS)


    project_info = pickle.load(open('project_info.p','rb'))


    targets = project_info['target_list'] 


    f = open(submit_file,'w')


    for target in targets:


        code = target[0][-3:]
        myms = target[2].rstrip('/')


        blind_prefix = 'img_'+myms+'_datablind'
        fits_mask1 = blind_prefix+'-combined1.mask.fits'
        masked_prefix = 'img_'+myms+'_datamask'
        pcal_prefix = 'img_'+myms+'_pcalmask'
        fits_mask2 = pcal_prefix+'-combined2.mask.fits'


        # ------------------------------------------------------------------------------
        # Automask wsclean 


        wsclean = gen.generate_syscall_wsclean(mslist=[myms],
                                imgname=blind_prefix,
                                datacol='DATA',
                                bda=True,
                                niter=30000,
                                mask='auto')

        f.write('singularity exec '+WSCLEAN_CONTAINER+' '+wsclean+'\n')


        # ------------------------------------------------------------------------------
        # Make FITS mask 


        makemask = gen.generate_syscall_makemask(blind_prefix,fits_mask1)


        f.write('singularity exec '+DDFACET_CONTAINER+' '+makemask+'\n')


        # ------------------------------------------------------------------------------
        # Masked wsclean 


        wsclean = gen.generate_syscall_wsclean(mslist=[myms],
                                imgname=masked_prefix,
                                datacol='DATA',
                                bda=True,
                                mask=fits_mask1)


        f.write('singularity exec '+WSCLEAN_CONTAINER+' '+wsclean+'\n')


        # ------------------------------------------------------------------------------
        # Predict 


        predict = gen.generate_syscall_predict(msname=myms,imgbase=masked_prefix)


        f.write('singularity exec '+WSCLEAN_CONTAINER+' '+predict+'\n')


        # ------------------------------------------------------------------------------
        # Self-calibrate phases 


        cubical = gen.generate_syscall_cubical(parset=PARSETS+'/phasecal.parset',
                    myms=myms,
                    prefix='pcal')


        f.write('singularity exec '+CUBICAL_CONTAINER+' '+cubical+'\n')


        # ------------------------------------------------------------------------------
        # Masked wsclean CORRECTED_DATA


        wsclean = gen.generate_syscall_wsclean(mslist=[myms],
                                imgname=pcal_prefix,
                                datacol='CORRECTED_DATA',
                                bda=True,
                                mask=fits_mask1)


        f.write('singularity exec '+WSCLEAN_CONTAINER+' '+wsclean+'\n')


        # ------------------------------------------------------------------------------
        # Make FITS mask 2


        makemask = gen.generate_syscall_makemask(pcal_prefix,fits_mask2)


        f.write('singularity exec '+DDFACET_CONTAINER+' '+makemask+'\n')


        # ------------------------------------------------------------------------------


    f.close()


if __name__ == "__main__":


    main()