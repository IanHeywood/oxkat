#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import os.path as o
import pickle
import sys
import glob
sys.path.append(o.abspath(o.join(o.dirname(sys.modules[__name__].__file__), "..")))


from oxkat import generate_jobs as gen
from oxkat import config as cfg


def main():
    
    # ------------------------------------------------------------------------------
    # Setup

    # Get paths from config and setup folders

    CWD = cfg.CWD
    OXKAT = cfg.OXKAT
    IMAGES = cfg.IMAGES
    PARSETS = cfg.PARSETS
    TOOLS = cfg.TOOLS
    LOGS = cfg.LOGS
    SCRIPTS = cfg.SCRIPTS

    gen.setup_dir(IMAGES)
    gen.setup_dir(LOGS)
    gen.setup_dir(SCRIPTS)


    # Set infrastructure and container path

    if len(sys.argv) == 1:
        print('Please specify infrastructure (idia / chpc / node)')
        sys.exit()

    if sys.argv[1].lower() == 'idia':
        infrastructure = 'idia'
        CONTAINER_PATH = cfg.IDIA_CONTAINER_PATH
    elif sys.argv[1].lower() == 'chpc':
        infrastructure = 'chpc'
        CONTAINER_PATH = cfg.CHPC_CONTAINER_PATH
    elif sys.argv[1].lower() == 'node':
        infrastructure = 'node'
        CONTAINER_PATH = cfg.NODE_CONTAINER_PATH


    # Get container and beam

    DDFACET_CONTAINER = gen.get_container(CONTAINER_PATH,'ddfacet-0.4.1')
#    BEAM = cfg.BEAM_L
    BEAM = '' 
    # Set names of the run files, open run file for writing

    submit_file = 'submit_DDFacet_job.sh'


    prefix = 'DDFpcal'
    dependency = None


    f = open(submit_file,'w')
    f.write('#!/usr/bin/env bash\n')


    project_info = pickle.load(open('project_info.p','rb'),encoding='latin1')


    targets = project_info['target_list'] 


    for target in targets:


        MASK = glob.glob('zoom*'+target[0]+'*mask.fits')[0]


        print(gen.now()+'Using FITS mask: '+MASK)


        code = target[0][-3:].replace('-','_').replace('.','p')
        myms = target[2].rstrip('/')
        mspat = '*'+target[0]+'*.ms'
        imgname = 'img_'+target[0]+'_'+prefix


        # ------------------------------------------------------------------------------
        # DDFacet 


        syscall = 'singularity exec '+DDFACET_CONTAINER+' '
        syscall += gen.generate_syscall_ddfacet(mspattern=mspat,
                    imgname = imgname,
                    chunkhours = 1,
                    beam = BEAM,
                    mask = MASK)
        syscall += ' ; singularity exec '+DDFACET_CONTAINER+' CleanSHM.py'     

        id_ddf = 'DDFact'+code

        run_command = gen.job_handler(syscall=syscall,
                    jobname = id_ddf,
                    infrastructure = infrastructure,
                    dependency = dependency,
                    slurm_config = cfg.SLURM_WSCLEAN,
                    pbs_config = cfg.PBS_WSCLEAN)

        f.write(run_command+'\n')



    f.close()


if __name__ == "__main__":


    main()