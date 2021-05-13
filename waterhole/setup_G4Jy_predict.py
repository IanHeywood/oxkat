
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

    USE_SINGULARITY = cfg.USE_SINGULARITY
    
    gen.preamble()
    print(gen.now()+'Predict visibilities from high resolution images')


    # ------------------------------------------------------------------------------
    #
    # Setup paths, required containers, infrastructure
    #
    # ------------------------------------------------------------------------------

    mslist = sorted(glob.glob('/idia/projects/G4Jy/1*/*/*.ms'))
    imgdir = '/idia/projects/G4Jy/1*/IMAGES/'

    OXKAT = cfg.OXKAT
    IMAGES = cfg.IMAGES
    SCRIPTS = cfg.SCRIPTS

    gen.setup_dir(IMAGES)
    gen.setup_dir(cfg.LOGS)
    gen.setup_dir(cfg.SCRIPTS)


    INFRASTRUCTURE, CONTAINER_PATH = gen.set_infrastructure(sys.argv)
    if CONTAINER_PATH is not None:
        CONTAINER_RUNNER='singularity exec '
    else:
        CONTAINER_RUNNER=''


    WSCLEAN_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.WSCLEAN_PATTERN,USE_SINGULARITY)


    # ------------------------------------------------------------------------------
    #
    # Image big MS list -- recipe definition
    #
    # ------------------------------------------------------------------------------


    steps = []
    codes = []
    ii = 1

    # Loop over Measurement Sets


    for i in range(0,len(mslist)):

    	myms = mslist[i]
    	field = myms.split('_')[-1].rstrip('.ms')
        code = gen.get_target_code(field)
        if code in codes:
            code += '_'+str(ii)
            ii += 1
        codes.append(code)
        gen.print_spacer()
        print(gen.now()+'MS        | '+myms)
        print(gen.now()+'Field     | '+field)
        print(gen.now()+'Code      | '+code)

        # Image prefix
        img_prefix = IMAGES+'/img_'+myms.split('/')[-1]+'_'+field+'_2GCr-1p5'

        step = {}
        step['step'] = i
        step['comment'] = 'Predict model visibilities'
        step['dependency'] = None
        step['id'] = 'WSDPR'+code
        step['slurm_config'] = cfg.SLURM_WSCLEAN
        step['pbs_config'] = cfg.PBS_WSCLEAN
        absmem = gen.absmem_helper(step,INFRASTRUCTURE,cfg.WSC_ABSMEM)
        syscall = CONTAINER_RUNNER+WSCLEAN_CONTAINER+' ' if USE_SINGULARITY else ''
        syscall += gen.generate_syscall_predict(msname = myms,imgbase = img_prefix,absmem = absmem)
        step['syscall'] = syscall
        steps.append(step)


    # ------------------------------------------------------------------------------
    #
    # Write the run file and kill file based on the recipe
    #
    # ------------------------------------------------------------------------------


    submit_file = 'submit_imaging_jobs.sh'
    kill_file = cfg.SCRIPTS+'/kill_imaging_jobs.sh'

    f = open(submit_file,'w')
    f.write('#!/usr/bin/env bash\n')
    f.write('export SINGULARITY_BINDPATH='+cfg.BINDPATH+'\n')

    id_list = []

    for step in steps:

        step_id = step['id']
        id_list.append(step_id)
        if step['dependency'] is not None:
            dependency = steps[step['dependency']]['id']
        else:
            dependency = None
        syscall = step['syscall']
        if 'slurm_config' in step.keys():
            slurm_config = step['slurm_config']
        else:
            slurm_config = cfg.SLURM_DEFAULTS
        if 'pbs_config' in step.keys():
            pbs_config = step['pbs_config']
        else:
            pbs_config = cfg.PBS_DEFAULTS
        comment = step['comment']

        run_command = gen.job_handler(syscall = syscall,
                        jobname = step_id,
                        infrastructure = INFRASTRUCTURE,
                        dependency = dependency,
                        slurm_config = slurm_config,
                        pbs_config = pbs_config)


        f.write('\n# '+comment+'\n')
        f.write(run_command)


    if INFRASTRUCTURE == 'idia' or INFRASTRUCTURE == 'hippo':
        kill = '\necho "scancel "$'+'" "$'.join(id_list)+' > '+kill_file+'\n'
        f.write(kill)
    elif INFRASTRUCTURE == 'chpc':
        kill = '\necho "qdel "$'+'" "$'.join(id_list)+' > '+kill_file+'\n'
        f.write(kill)
    
    f.close()

    gen.make_executable(submit_file)

    gen.print_spacer()
    print(gen.now()+'Created '+submit_file)
    gen.print_spacer()

    # ------------------------------------------------------------------------------



if __name__ == "__main__":


    main()
