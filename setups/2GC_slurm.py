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
    WSCLEAN_CONTAINER = gen.WSCLEAN_CONTAINER
    CUBICAL_CONTAINER = gen.CUBICAL_CONTAINER
    DDFACET_CONTAINER = gen.DDFACET_CONTAINER 


    submit_file = 'submit_2GC_jobs.sh'
    kill_file = 'kill_2GC_jobs.sh'


    gen.setup_dir(SCRIPTS)
    gen.setup_dir(LOGS)


    with open('project_info.p','rb') as f:
        project_info = pickle.load(f,encoding='latin1')


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


        slurmfile = SCRIPTS+'/slurm_wsclean_blind_'+code+'.sh'
        logfile = LOGS+'/slurm_wsclean_blind_'+code+'.log'

        syscall = 'singularity exec '+WSCLEAN_CONTAINER+' '
        syscall += gen.generate_syscall_wsclean(mslist=[myms],
                                imgname=blind_prefix,
                                datacol='DATA',
                                bda=True,
                                niter=30000,
                                mask='auto')


        gen.write_slurm(opfile=slurmfile,
                    jobname=code+'blind',
                    logfile=logfile,
                    syscall=syscall)


        job_id_blind = 'BLIND_'+code
        syscall = job_id_blind+"=`sbatch "+slurmfile+" | awk '{print $4}'`"
        f.write(syscall+'\n')


        # ------------------------------------------------------------------------------
        # Make FITS mask 


        slurmfile = SCRIPTS+'/slurm_makemask1_'+code+'.sh'
        logfile = LOGS+'/slurm_makemask1_'+code+'.log'


        syscall1,syscall2 = gen.generate_syscall_makemask(blind_prefix,fits_mask1)


        syscall = 'singularity exec '+DDFACET_CONTAINER+' '+syscall1
        syscall += 'singularity exec '+CUBICAL_CONTAINER+' '+syscall2


        gen.write_slurm(opfile=slurmfile,
                    jobname=code+'mask1',
                    logfile=logfile,
                    syscall=syscall)


        job_id_makemask1 = 'MAKEMASK1_'+code
        syscall = job_id_makemask1+"=`sbatch -d afterok:${"+job_id_blind+"} "+slurmfile+" | awk '{print $4}'`"
        f.write(syscall+'\n')


        # ------------------------------------------------------------------------------
        # Masked wsclean 


        slurmfile = SCRIPTS+'/slurm_wsclean_mask1_'+code+'.sh'
        logfile = LOGS+'/slurm_wsclean_mask1_'+code+'.log'


        syscall = 'singularity exec '+WSCLEAN_CONTAINER+' '
        syscall += gen.generate_syscall_wsclean(mslist=[myms],
                                imgname=masked_prefix,
                                datacol='DATA',
                                bda=True,
                                mask=fits_mask1)


        gen.write_slurm(opfile=slurmfile,
                    jobname=code+'dmask',
                    logfile=logfile,
                    syscall=syscall)


        job_id_wsmask1 = 'IMGMASK1_'+code
        syscall = job_id_wsmask1+"=`sbatch -d afterok:${"+job_id_makemask1+"} "+slurmfile+" | awk '{print $4}'`"
        f.write(syscall+'\n')


        # ------------------------------------------------------------------------------
        # Predict 


        slurmfile = SCRIPTS+'/slurm_wsclean_predict1_'+code+'.sh'
        logfile = LOGS+'/slurm_wsclean_predict1_'+code+'.log'


        syscall = 'singularity exec '+WSCLEAN_CONTAINER+' '
        syscall += gen.generate_syscall_predict(msname=myms,imgbase=masked_prefix)


        gen.write_slurm(opfile=slurmfile,
                    jobname=code+'pdct1',
                    logfile=logfile,
                    syscall=syscall)


        job_id_predict1 = 'PREDICT1_'+code
        syscall = job_id_predict1+"=`sbatch -d afterok:${"+job_id_wsmask1+"} "+slurmfile+" | awk '{print $4}'`"
        f.write(syscall+'\n')


        # ------------------------------------------------------------------------------
        # Self-calibrate phases 


        slurmfile = SCRIPTS+'/slurm_cubical1_'+code+'.sh'
        logfile = LOGS+'/slurm_cubical1_'+code+'.log'


        syscall = 'singularity exec '+CUBICAL_CONTAINER+' '
        syscall += gen.generate_syscall_cubical(parset=PARSETS+'/phasecal.parset',
                    myms=myms,
                    prefix='pcal')


        gen.write_slurm(opfile=slurmfile,
                    jobname=code+'pcal1',
                    logfile=logfile,
                    syscall=syscall)


        job_id_cubical1 = 'CUBICAL1_'+code
        syscall = job_id_cubical1+"=`sbatch -d afterok:${"+job_id_predict1+"} "+slurmfile+" | awk '{print $4}'`"
        f.write(syscall+'\n')


        # ------------------------------------------------------------------------------
        # Masked wsclean CORRECTED_DATA


        slurmfile = SCRIPTS+'/slurm_wsclean_pcal1_'+code+'.sh'
        logfile = LOGS+'/slurm_wsclean_pcal1_'+code+'.log'


        syscall = 'singularity exec '+WSCLEAN_CONTAINER+' '
        syscall += gen.generate_syscall_wsclean(mslist=[myms],
                                imgname=pcal_prefix,
                                datacol='CORRECTED_DATA',
                                bda=True,
                                mask=fits_mask1)


        gen.write_slurm(opfile=slurmfile,
                    jobname=code+'cmask',
                    logfile=logfile,
                    syscall=syscall)


        job_id_wsmask2 = 'IMGMASK2_'+code
        syscall = job_id_wsmask2+"=`sbatch -d afterok:${"+job_id_cubical1+"} "+slurmfile+" | awk '{print $4}'`"
        f.write(syscall+'\n')


        # ------------------------------------------------------------------------------
        # Make FITS mask 2


        slurmfile = SCRIPTS+'/slurm_makemask2_'+code+'.sh'
        logfile = LOGS+'/slurm_makemask2_'+code+'.log'


        syscall1,syscall2 = gen.generate_syscall_makemask(pcal_prefix,fits_mask2)


        syscall = 'singularity exec '+DDFACET_CONTAINER+' '+syscall1
        syscall += 'singularity exec '+CUBICAL_CONTAINER+' '+syscall2


        gen.write_slurm(opfile=slurmfile,
                    jobname=code+'mask2',
                    logfile=logfile,
                    syscall=syscall)


        job_id_makemask2 = 'MAKEMASK2_'+code
        syscall = job_id_makemask2+"=`sbatch -d afterok:${"+job_id_wsmask2+"} "+slurmfile+" | awk '{print $4}'`"
        f.write(syscall+'\n')


        # ------------------------------------------------------------------------------

    kill = 'echo "scancel "$'+job_id_blind+'" "$'+job_id_makemask1+'" "$'+job_id_wsmask1+'" "$'+job_id_predict1+'" "$'+job_id_cubical1+'" "$'+job_id_wsmask2+'" "$'+job_id_makemask2+' > '+kill_file

    f.write(kill+'\n')

    f.close()


if __name__ == "__main__":


    main()