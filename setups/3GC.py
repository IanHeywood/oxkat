#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import glob
import os.path as o
import pickle
import sys
sys.path.append(o.abspath(o.join(o.dirname(sys.modules[__name__].__file__), "..")))


from oxkat import generate_jobs as gen
from oxkat import config as cfg


def main():

    # ------------------------------------------------------------------------------
    # Setup


    INFRASTRUCTURE, CONTAINER_PATH = gen.set_infrastructure(sys.argv)


    if INFRASTRUCTURE == 'idia':
        myNCPU = 8
    elif INFRASTRUCTURE == 'chpc':
        myNCPU = 23
    else:
        myNCPU = 40


    # Get paths from config and setup folders

    CWD = cfg.CWD
    OXKAT = cfg.OXKAT
    PARSETS = cfg.PARSETS
    TOOLS = cfg.TOOLS
    GAINTABLES = cfg.GAINTABLES
    IMAGES = cfg.IMAGES
    LOGS = cfg.LOGS
    SCRIPTS = cfg.SCRIPTS


    gen.setup_dir(LOGS)
    gen.setup_dir(SCRIPTS)
    gen.setup_dir(IMAGES)
    gen.setup_dir(GAINTABLES)

    # Enable running without containers
    if CONTAINER_PATH is not None:
        CONTAINER_RUNNER='singularity exec '
    else:
        CONTAINER_RUNNER=''

    # Get containers needed for this script

    DDFACET_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.DDFACET_PATTERN)
    KILLMS_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.KILLMS_PATTERN)

    # Set names of the run and kill files, open run file for writing

    submit_file = 'submit_3GC_jobs.sh'

    f = open(submit_file,'w')
    f.write('#!/usr/bin/env bash\n')


    # Get target info from project_info.p

    project_info = pickle.load(open('project_info.p','rb'),encoding='latin1')

    target_ids = project_info['target_ids'] 
    target_names = project_info['target_names']
    target_ms = project_info['target_ms']

    # Loop over targets

    codes = []
    ii = 1


    for tt in range(0,len(target_ids)):


        targetname = target_names[tt]
        myms = target_ms[tt]


        if not o.isdir(myms):

            print('------------------------------------------------------')
            print(gen.now()+myms+' not found, skipping '+targetname)

        else:
            
            filename_targetname = gen.scrub_target_name(targetname)

            code = gen.get_target_code(targetname)
            if code in codes:
                code += '_'+str(ii)
                ii += 1
            codes.append(code)


            mask1 = sorted(glob.glob(IMAGES+'/*'+filename_targetname+'*.mask1.zoom*.fits'))
            if len(mask1) > 0:
                mask = mask1[0]
            else:
                mask = 'auto'


            region = glob.glob('*'+targetname+'*.reg')
            if len(region) == 0:
                print(gen.now()+'Please provide a region file')
                sys.exit()
            else:
                region = region[0]

            print('------------------------------------------------------')
            print(gen.now()+'Target:       '+targetname)
            print(gen.now()+'MS:           '+myms)
            print(gen.now()+'Using mask:   '+mask)
            print(gen.now()+'Using region: '+region)

            f.write('\n# '+targetname+'\n')
        
            kill_file = SCRIPTS+'/kill_3GC_jobs_'+filename_targetname+'.sh'


            ddf_img_prefix = IMAGES+'/img_'+myms+'_DDFpcal'
            kms_img_prefix = IMAGES+'/img_'+myms+'_DDFkMS'


            # Initialise a list to hold all the job IDs

            id_list = []


            # ------------------------------------------------------------------------------
            # STEP 1: 
            # DDFacet on CORRECTED_DATA column


            id_ddfacet1 = 'DDCMA'+code
            id_list.append(id_ddfacet1)

            syscall = CONTAINER_RUNNER+DDFACET_CONTAINER+' '
            syscall += gen.generate_syscall_ddfacet(mspattern=myms,
                        imgname=ddf_img_prefix,
                        ncpu=myNCPU,
                        mask=mask,
                        sparsification='100,30,10,2')

            run_command = gen.job_handler(syscall=syscall,
                        jobname=id_ddfacet1,
                        infrastructure=INFRASTRUCTURE,
                        slurm_config = cfg.SLURM_HIGHMEM,
                        pbs_config = cfg.PBS_WSCLEAN)

            f.write(run_command)


            # ------------------------------------------------------------------------------
            # STEP 2: 
            # Run killMS 


            id_killms = 'KILMS'+code
            id_list.append(id_killms)

            syscall = CONTAINER_RUNNER+KILLMS_CONTAINER+' '
            syscall += 'python3 '+TOOLS+'/reg2npy.py '+region+'\n '
            syscall += CONTAINER_RUNNER+KILLMS_CONTAINER+' '
            syscall += gen.generate_syscall_killms(myms=myms,
                        baseimg=ddf_img_prefix,
                        ncpu=myNCPU,
                        outsols='killms-cohjones',
                        nodesfile=region+'.npy')

            run_command = gen.job_handler(syscall=syscall,
                        jobname=id_killms,
                        dependency=id_ddfacet1,
                        infrastructure=INFRASTRUCTURE,
                        slurm_config = cfg.SLURM_HIGHMEM,
                        pbs_config = cfg.PBS_WSCLEAN)

            f.write(run_command)

            # ------------------------------------------------------------------------------
            # STEP 3: 
            # DDFacet on CORRECTED_DATA column, apply killMS solutions


            id_ddfacet2 = 'DDKMA'+code
            id_list.append(id_ddfacet1)

            syscall = CONTAINER_RUNNER+DDFACET_CONTAINER+' '
            syscall += gen.generate_syscall_ddfacet(mspattern=myms,
                        imgname=kms_img_prefix,
                        chunkhours=1,
                        ncpu=myNCPU,
                        initdicomodel=ddf_img_prefix+'.DicoModel',
                        hogbom_maxmajoriter=0,
                        hogbom_maxminoriter=1000,
                        mask=mask,
                        ddsols='killms-cohjones')

            run_command = gen.job_handler(syscall=syscall,
                        jobname=id_ddfacet2,
                        dependency=id_killms,
                        infrastructure=INFRASTRUCTURE,
                        slurm_config = cfg.SLURM_HIGHMEM,
                        pbs_config = cfg.PBS_WSCLEAN)

            f.write(run_command)


            # ------------------------------------------------------------------------------


            if INFRASTRUCTURE == 'idia':
                kill = 'echo "scancel "$'+'" "$'.join(id_list)+' > '+kill_file+'\n'
                f.write(kill)
            elif INFRASTRUCTURE == 'chpc':
                kill = 'echo "qdel "$'+'" "$'.join(id_list)+' > '+kill_file+'\n'
                f.write(kill)

    f.close()


if __name__ == "__main__":


    main()
