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
    CASA_CONTAINER = gen.CASA_CONTAINER
    WSCLEAN_CONTAINER = gen.WSCLEAN_CONTAINER
    DDFACET_CONTAINER = gen.DDFACET_CONTAINER
    XCASA_CONTAINER = gen.XCASA_CONTAINER
    XWSCLEAN_CONTAINER = gen.XWSCLEAN_CONTAINER
    XDDFACET_CONTAINER = gen.XDDFACET_CONTAINER


    submit_file = 'submit_2GC_jobs.sh'
    kill_file = 'kill_2GC_jobs.sh'
    run_file = 'run_2GC_jobs.sh'


    gen.setup_dir(SCRIPTS)
    gen.setup_dir(LOGS)


    with open('project_info.p','rb') as f:
        project_info = pickle.load(f,encoding='latin1')


    targets = project_info['target_list'] 


    f = open(submit_file,'w')
    g = open(run_file,'w')


    f.write('#!/usr/bin/env bash\n')
    g.write('#!/usr/bin/env bash\n')


    for target in targets:


        code = target[0][-3:].replace('-','_').replace('.','p')
        myms = target[2].rstrip('/')

    
        kill_file = SCRIPTS+'/kill_2GC_jobs_'+target[0].replace('+','p')+'.sh'


        blind_prefix = 'img_'+myms+'_data'
        pcal_prefix = 'img_'+myms+'_pcal'


        # ------------------------------------------------------------------------------
        # Automask wsclean 


        slurmfile = SCRIPTS+'/slurm_wsclean_blind_'+code+'.sh'
        logfile = LOGS+'/slurm_wsclean_blind_'+code+'.log'

        syscall = 'singularity exec '+WSCLEAN_CONTAINER+' '
        syscall += gen.generate_syscall_wsclean(mslist=[myms],
                                imgname=blind_prefix,
                                datacol='DATA',
                                bda=True,
                                niter=60000,
                                mask='auto')


        gen.write_slurm(opfile=slurmfile,
                    jobname=code+'wdata',
                    logfile=logfile,
                    syscall=syscall)


        syscall = syscall.replace(WSCLEAN_CONTAINER,XWSCLEAN_CONTAINER)
        g.write(syscall+'\n')


        job_id_blind = 'BLIND_'+code
        syscall = job_id_blind+"=`sbatch "+slurmfile+" | awk '{print $4}'`"
        f.write(syscall+'\n')


        # ------------------------------------------------------------------------------
        # Predict 


        slurmfile = SCRIPTS+'/slurm_wsclean_predict1_'+code+'.sh'
        logfile = LOGS+'/slurm_wsclean_predict1_'+code+'.log'


        syscall = 'singularity exec '+WSCLEAN_CONTAINER+' '
        syscall += gen.generate_syscall_predict(msname=myms,imgbase=blind_prefix)


        gen.write_slurm(opfile=slurmfile,
                    jobname=code+'pdct1',
                    logfile=logfile,
                    syscall=syscall)


        syscall = syscall.replace(WSCLEAN_CONTAINER,XWSCLEAN_CONTAINER)
        g.write(syscall+'\n')


        job_id_predict1 = 'PREDICT1_'+code
        syscall = job_id_predict1+"=`sbatch -d afterok:${"+job_id_blind+"} "+slurmfile+" | awk '{print $4}'`"
        f.write(syscall+'\n')


        # ------------------------------------------------------------------------------
        # Self-calibrate phases 


        slurmfile = SCRIPTS+'/slurm_phasecal1_'+code+'.sh'
        logfile = LOGS+'/slurm_phasecal1_'+code+'.log'


        syscall = 'singularity exec '+CASA_CONTAINER+' '
        syscall += 'casa -c '+OXKAT+'/casa_selfcal_target_phases.py '+myms+' --nologger --log2term --nogui\n'


        gen.write_slurm(opfile=slurmfile,
                    jobname=code+'pcal1',
                    logfile=logfile,
                    syscall=syscall)


        syscall = syscall.replace(CASA_CONTAINER,XCASA_CONTAINER)
        g.write(syscall+'\n')


        job_id_phasecal1 = 'PHASECAL1_'+code
        syscall = job_id_phasecal1+"=`sbatch -d afterok:${"+job_id_predict1+"} "+slurmfile+" | awk '{print $4}'`"
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
                                mask='auto')


        gen.write_slurm(opfile=slurmfile,
                    jobname=code+'wcorr',
                    logfile=logfile,
                    syscall=syscall)


        syscall = syscall.replace(WSCLEAN_CONTAINER,XWSCLEAN_CONTAINER)
        g.write(syscall+'\n')


        job_id_blind2 = 'BLIND2_'+code
        syscall = job_id_blind2+"=`sbatch -d afterok:${"+job_id_phasecal1+"} "+slurmfile+" | awk '{print $4}'`"
        f.write(syscall+'\n')


        # ------------------------------------------------------------------------------

        # Make FITS mask 


        slurmfile = SCRIPTS+'/slurm_makemask1_'+code+'.sh'
        logfile = LOGS+'/slurm_makemask1_'+code+'.log'


        syscall,fitsmask = gen.generate_syscall_makemask(pcal_prefix,thresh=5.5)
        syscall = 'singularity exec '+DDFACET_CONTAINER+' '+syscall


        gen.write_slurm(opfile=slurmfile,
                    jobname=code+'mask1',
                    logfile=logfile,
                    syscall=syscall)


        syscall = syscall.replace(DDFACET_CONTAINER,XDDFACET_CONTAINER)
        g.write(syscall+'\n')


        job_id_makemask1 = 'MAKEMASK1_'+code
        syscall = job_id_makemask1+"=`sbatch -d afterok:${"+job_id_blind2+"} "+slurmfile+" | awk '{print $4}'`"        
        f.write(syscall+'\n')


        # ------------------------------------------------------------------------------


        kill = 'echo "scancel "$'+job_id_blind+'" "$'+job_id_predict1+'" "$'+job_id_phasecal1+'" "$'+job_id_blind2+'" "$'+job_id_makemask1+' >> '+kill_file

        f.write(kill+'\n')


    f.close()
    g.close()


if __name__ == "__main__":


    main()