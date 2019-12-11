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
    TOOLS = gen.TOOLS
    DDFACET_CONTAINER = gen.DDFACET_CONTAINER
    SOURCEFINDER_CONTAINER = gen.SOURCEFINDER_CONTAINER
    CLUSTERCAT_CONTAINER = gen.CLUSTERCAT_CONTAINER
    KILLMS_CONTAINER = gen.KILLMS_CONTAINER 


    BEAM = '/users/ianh/Beams/hvfix/meerkat_pb_jones_cube_95channels_$(xy)_$(reim).fits'
    MASK = glob.glob('*mask.fits')[0]


    print('Using FITS mask: '+MASK)


    submit_file = 'submit_3GC-beam_jobs.sh'
    kill_file = 'kill_3GC-beam_jobs.sh'


    gen.setup_dir(SCRIPTS)
    gen.setup_dir(LOGS)


    with open('project_info.p','rb') as f:
        project_info = pickle.load(f,encoding='latin1')


    targets = project_info['target_list'] 


    f = open(submit_file,'w')


    for target in targets:


        code = target[0][-3:].replace('-','_').replace('.','p')
        mspat = '*'+target[0]+'*.ms'


        ddf1_prefix = 'img_'+target[0]+'_DDF_corr_beam'


        # ------------------------------------------------------------------------------
        # DDFacet


        slurmfile = SCRIPTS+'/slurm_ddf_corr_'+code+'.sh'
        logfile = LOGS+'/slurm_ddf_corr_'+code+'.log'


        syscall = 'singularity exec '+DDFACET_CONTAINER+' '
        syscall += gen.generate_syscall_ddfacet(mspattern=mspat,
                    imgname=ddf1_prefix,
                    chunkhours=1,
                    beam=BEAM,
                    mask=MASK)


        gen.write_slurm(opfile=slurmfile,
                    jobname=code+'_DDF1',
                    logfile=logfile,
                    syscall=syscall,
                    mem='480GB',
                    partition='HighMem')


        job_id_ddf1 = 'DDF1_'+code
        syscall = job_id_ddf1+"=`sbatch "+slurmfile+" | awk '{print $4}'`"
        f.write(syscall+'\n')


        # ------------------------------------------------------------------------------
        # PyBDSF


        slurmfile = SCRIPTS+'/slurm_pybdsf_'+code+'.sh'
        logfile = LOGS+'/slurm_pydsf_'+code+'.log'


        syscall = 'singularity exec '+SOURCEFINDER_CONTAINER+' '
        syscall2,bdsfcat = gen.generate_syscall_pybdsf(ddf1_prefix+'.app.restored.fits',
                        catalogtype='srl',
                        catalogformat='fits')
        syscall += syscall2


        gen.write_slurm(opfile=slurmfile,
                    jobname=code+'pbdsf',
                    logfile=logfile,
                    syscall=syscall)


        job_id_bdsf = 'BDSF_'+code
        syscall = job_id_bdsf+"=`sbatch -d afterok:${"+job_id_ddf1+"} "+slurmfile+" | awk '{print $4}'`"
        f.write(syscall+'\n')


        # ------------------------------------------------------------------------------
        # Identify tessel centres


        # slurmfile = SCRIPTS+'/slurm_dEid_'+code+'.sh'
        # logfile = LOGS+'/slurm_dEid_'+code+'.log'


        # syscall = 'singularity exec '+SOURCEFINDER_CONTAINER+' '
        # syscall += 'python '+TOOLS+'/identify_dE_directions.py'


        # gen.write_slurm(opfile=slurmfile,
        #             jobname=code+'dEid',
        #             logfile=logfile,
        #             syscall=syscall)


        # job_id_deid = 'DEID_'+code
        # syscall = job_id_deid+"=`sbatch -d afterok:${"+job_id_bdsf+"} "+slurmfile+" | awk '{print $4}'`"
        # f.write(syscall+'\n')


        # ------------------------------------------------------------------------------
        # Run ClusterCat


        slurmfile = SCRIPTS+'/slurm_cluster_'+code+'.sh'
        logfile = LOGS+'/slurm_cluster_'+code+'.log'


        syscall = 'singularity exec '+DDFACET_CONTAINER+' '
        syscall1,clusterfile = gen.generate_syscall_clustercat(bdsfcat,ndir=7)
        syscall += syscall1


        gen.write_slurm(opfile=slurmfile,
                    jobname=code+'clstr',
                    logfile=logfile,
                    syscall=syscall)


        job_id_cluster = 'CLSTR_'+code
        syscall = job_id_cluster+"=`sbatch -d afterok:${"+job_id_bdsf+"} "+slurmfile+" | awk '{print $4}'`"
        f.write(syscall+'\n')

        # ------------------------------------------------------------------------------

    kill = 'echo "scancel "$'+job_id_ddf1+' > '+kill_file

    f.write(kill+'\n')

    f.close()


if __name__ == "__main__":


    main()