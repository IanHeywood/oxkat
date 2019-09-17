#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import os.path as o
import pickle
import sys
import glob
sys.path.append(o.abspath(o.join(o.dirname(sys.modules[__name__].__file__), "..")))


from oxkat import generate_jobs as gen


def main():
    
    CWD = gen.CWD
    OXKAT = gen.OXKAT
    PARSETS = gen.PARSETS
    SCRIPTS = gen.SCRIPTS
    LOGS = gen.LOGS
    DDFACET_CONTAINER = gen.DDFACET_CONTAINER 


    BEAM = '/users/ianh/Beams/hvfix/MeerKAT_VBeam_10MHz_53Chans_$(xy)_$(reim).fits'
    MASK = glob.glob('*mask.fits')[0]

    print('Using FITS mask: '+MASK)


    submit_file = 'submit_3GC-beam_jobs.sh'
    kill_file = 'kill_3GC-beam_jobs.sh'


    gen.setup_dir(SCRIPTS)
    gen.setup_dir(LOGS)


#    project_info = pickle.load(open('project_info.p','rb'))


 #   targets = project_info['target_list'] 





    f = open(submit_file,'w')


    for target in ['']:

        code = 'X12'

#        code = target[0][-3:]
#        myms = target[2].rstrip('/')


        ddf1_prefix = 'img_XMM12_DDFbeamHVfix'


        # ------------------------------------------------------------------------------
        # DDFacet


        slurmfile = SCRIPTS+'/slurm_ddf_corr_'+code+'.sh'
        logfile = LOGS+'/slurm_ddf_corr_'+code+'.log'


        syscall = 'singularity exec '+DDFACET_CONTAINER+' '
        syscall += gen.generate_syscall_ddfacet(mspattern='*.ms',
                    imgname=ddf1_prefix,
                    chunkhours=2,
                    beam=BEAM,
                    mask=MASK)


        gen.write_slurm(opfile=slurmfile,
                    jobname=code+'ddfbm',
                    logfile=logfile,
                    syscall=syscall,
                    mem='480GB',
                    partition='HighMem')


        job_id_ddf1 = 'DDF1_'+code
        syscall = job_id_ddf1+"=`sbatch "+slurmfile+" | awk '{print $4}'`"
        f.write(syscall+'\n')


        # # ------------------------------------------------------------------------------
        # # Make FITS mask 


        # slurmfile = SCRIPTS+'/slurm_makemask1_'+code+'.sh'
        # logfile = LOGS+'/slurm_makemask1_'+code+'.log'


        # syscall1,syscall2 = gen.generate_syscall_makemask(blind_prefix,fits_mask1)


        # syscall = 'singularity exec '+DDFACET_CONTAINER+' '+syscall1
        # syscall += 'singularity exec '+CUBICAL_CONTAINER+' '+syscall2


        # gen.write_slurm(opfile=slurmfile,
        #             jobname=code+'mask1',
        #             logfile=logfile,
        #             syscall=syscall)


        # job_id_makemask1 = 'MAKEMASK1_'+code
        # syscall = job_id_makemask1+"=`sbatch -d afterok:${"+job_id_blind+"} "+slurmfile+" | awk '{print $4}'`"
        # f.write(syscall+'\n')



        # ------------------------------------------------------------------------------

    kill = 'echo "scancel "$'+job_id_ddf1+' > '+kill_file

    f.write(kill+'\n')

    f.close()


if __name__ == "__main__":


    main()