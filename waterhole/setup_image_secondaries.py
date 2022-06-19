#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import glob
import json
import os.path as o
import sys
sys.path.append(o.abspath(o.join(o.dirname(sys.modules[__name__].__file__), "..")))


from oxkat import generate_jobs as gen
from oxkat import config as cfg


def main():

    USE_SINGULARITY = cfg.USE_SINGULARITY
    
    gen.preamble()
    print(gen.now()+'Imaging secondary calibrators')


    # ------------------------------------------------------------------------------
    #
    # Setup paths, required containers, infrastructure
    #
    # ------------------------------------------------------------------------------


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


    # Get secondary calibrator information from project info json file

    with open('project_info.json') as f:
        project_info = json.load(f)

    myms = project_info['working_ms']
    pcal_names = project_info['secondary_names']
    pcal_ids = project_info['secondary_ids']

    if cfg.PRE_FIELDS != '':
        from oxkat import user_field_handler as ufh
        pcal_names = ufh.user_pcals
        pcal_ids = ufh.user_pcal_ids

    # ------------------------------------------------------------------------------
    #
    # Image calibrators -- recipe definition
    #
    # ------------------------------------------------------------------------------


    cal_steps = []
    codes = []
    ii = 1

    # Loop over secondaries

    for i in range(0,len(pcal_ids)):

        field = pcal_ids[i]
        calname = pcal_names[i]


        steps = []        
        filename_calname = gen.scrub_target_name(calname)


        code = gen.get_target_code(calname)
        if code in codes:
            code += '_'+str(ii)
            ii += 1
        codes.append(code)
    

        gen.print_spacer()
        print(gen.now()+'Secondary | '+calname)
        print(gen.now()+'Code      | '+code)


        # Image prefix
        img_prefix = IMAGES+'/img_'+myms+'_'+filename_calname+'_corrblind'


        step = {}
        step['step'] = i
        step['comment'] = 'Run wsclean, blind deconvolution of the CORRECTED_DATA for '+calname
        if i == 0:
            step['dependency'] = None
        else:
            step['dependency'] = i-1
        step['id'] = 'WSCMA'+code
        step['slurm_config'] = cfg.SLURM_WSCLEAN
        step['pbs_config'] = cfg.PBS_WSCLEAN
        syscall = CONTAINER_RUNNER+WSCLEAN_CONTAINER+' ' if USE_SINGULARITY else ''
        syscall = 'singularity exec '+WSCLEAN_CONTAINER+' '
        syscall += gen.generate_syscall_wsclean(mslist = [myms],
                                imgname = img_prefix,
                                field = field,
                                datacol = 'CORRECTED_DATA',
                                imsize = 8192,
                                niter = 40000,
                                gain = 0.2,
                                mgain = 0.9, 
                                bda = True,
                                mask = 'none')
        step['syscall'] = syscall
        steps.append(step)



    # ------------------------------------------------------------------------------
    #
    # Write the run file and kill file based on the recipe
    #
    # ------------------------------------------------------------------------------


    submit_file = 'submit_image_secondary_jobs.sh'
    kill_file = cfg.SCRIPTS+'/kill_image_secondary_jobs.sh'

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
