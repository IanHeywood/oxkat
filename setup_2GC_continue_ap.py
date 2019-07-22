#!/usr/bin/env python
# ian.heywood@astro.ox.ac.uk


import pickle
from oxkat import generate_jobs as gen


def main():
    
    CWD = gen.CWD
    OXKAT = gen.OXKAT
    PARSETS = gen.PARSETS
    SCRIPTS = gen.SCRIPTS
    LOGS = gen.LOGS
    WSCLEAN_CONTAINER = gen.WSCLEAN_CONTAINER
    CUBICAL_CONTAINER = gen.CUBICAL_CONTAINER
    DDFACET_CONTAINER = gen.DDFACET_CONTAINER 


    submit_file = 'submit_2GC_jobs2.sh'
    kill_file = 'kill_2GC_jobs2.sh'


    gen.setup_dir(SCRIPTS)
    gen.setup_dir(LOGS)


    project_info = pickle.load(open('project_info.p','rb'))


    targets = project_info['target_list'] 


    f = open(submit_file,'w')


    for target in targets:


        code = target[0][-3:]
        myms = target[2].rstrip('/')


        blind_prefix = 'img_'+myms+'_datablind'
        fits_mask1 = blind_prefix+'-MFS-image.fits.mask.fits'
        masked_prefix = 'img_'+myms+'_datamask'
        pcal_prefix = 'img_'+myms+'_pcalmask'
        fits_mask2 = pcal_prefix+'-MFS-image.fits.mask.fits'
        apcal_prefix = 'img_'+myms+'_apcalmask2'


        # ------------------------------------------------------------------------------
        # Predict 


        slurmfile = SCRIPTS+'/slurm_wsclean_predict2_'+code+'.sh'
        logfile = LOGS+'/slurm_predict2_'+code+'.log'


        predict = gen.generate_syscall_predict(msname=myms,imgbase=pcal_prefix)


        gen.write_slurm(opfile=slurmfile,
                    jobname=code+'pdct2',
                    logfile=logfile,
                    container=WSCLEAN_CONTAINER,
                    syscall=predict)


        job_id_predict2 = 'PREDICT1_'+code
        syscall = job_id_predict2+"=`sbatch "+slurmfile+" | awk '{print $4}'`"
        f.write(syscall+'\n')



        # ------------------------------------------------------------------------------
        # Self-calibrate amplitudes and phases 


        slurmfile = SCRIPTS+'/slurm_cubical2_'+code+'.sh'
        logfile = LOGS+'/slurm_cubical2_'+code+'.log'


        cubical = gen.generate_syscall_cubical(parset=PARSETS+'/apcal.parset',
                    myms=myms,
                    prefix='apcal')


        gen.write_slurm(opfile=slurmfile,
                    jobname=code+'acal1',
                    logfile=logfile,
                    container=CUBICAL_CONTAINER,
                    syscall=cubical)


        job_id_cubical2 = 'CUBICAL2_'+code
        syscall = job_id_cubical2+"=`sbatch -d afterok:${"+job_id_predict2+"} "+slurmfile+" | awk '{print $4}'`"
        f.write(syscall+'\n')


        # ------------------------------------------------------------------------------
        # Masked wsclean 


        slurmfile = SCRIPTS+'/slurm_wsclean_mask2_'+code+'.sh'
        logfile = LOGS+'/slurm_mask2_'+code+'.log'


        wsclean = gen.generate_syscall_wsclean(mslist=[myms],
                                imgname=apcal_prefix,
                                datacol='CORRECTED_DATA',
                                bda=True,
                                mask=fits_mask2)


        gen.write_slurm(opfile=slurmfile,
                    jobname=code+'cmask',
                    logfile=logfile,
                    container=WSCLEAN_CONTAINER,
                    syscall=wsclean)


        job_id_wsmask2 = 'IMGMASK2_'+code
        syscall = job_id_wsmask2+"=`sbatch -d afterok:${"+job_id_cubical2+"} "+slurmfile+" | awk '{print $4}'`"
        f.write(syscall+'\n')


        # ------------------------------------------------------------------------------

    kill = 'echo "scancel "$'+job_id_predict2+'" "$'+job_id_cubical2+'" "$'+job_id_wsmask2+' > '+kill_file

    f.write(kill+'\n')

    f.close()


if __name__ == "__main__":


    main()