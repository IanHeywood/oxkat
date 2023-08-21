#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk
# If peeling goes wrong you can use this script to restore the CORRECTED_DATA column


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
    print(gen.col()+'Repredict and recalibrate (2GC)')
    gen.print_spacer()

    # ------------------------------------------------------------------------------
    #
    # Setup paths, required containers, infrastructure
    #
    # ------------------------------------------------------------------------------


    OXKAT = cfg.OXKAT
    DATA = cfg.DATA
    GAINTABLES = cfg.GAINTABLES
    IMAGES = cfg.IMAGES
    SCRIPTS = cfg.SCRIPTS

    gen.setup_dir(GAINTABLES)
    gen.setup_dir(IMAGES)
    gen.setup_dir(cfg.LOGS)
    gen.setup_dir(cfg.SCRIPTS)


    INFRASTRUCTURE, CONTAINER_PATH = gen.set_infrastructure(sys.argv)
    if CONTAINER_PATH is not None:
        CONTAINER_RUNNER='singularity exec '
    else:
        CONTAINER_RUNNER=''


    CUBICAL_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.CUBICAL_PATTERN,USE_SINGULARITY)
    OWLCAT_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.OWLCAT_PATTERN,USE_SINGULARITY)
    WSCLEAN_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.WSCLEAN_PATTERN,USE_SINGULARITY)


    # Get target information from project info json file

    with open('project_info.json') as f:
        project_info = json.load(f)

    target_ids = project_info['target_ids'] 
    target_names = project_info['target_names']
    target_ms = project_info['target_ms']


    # ------------------------------------------------------------------------------
    #
    # 2GC recipe definition
    #
    # ------------------------------------------------------------------------------


    target_steps = []
    codes = []
    ii = 1
    stamp = gen.timenow()


    # Loop over targets

    for tt in range(0,len(target_ids)):

        targetname = target_names[tt]
        myms = target_ms[tt]

        # Image prefixes
        data_img_prefix = IMAGES+'/img_'+myms+'_datamask'
        have_img = glob.glob(data_img_prefix+'*.fits')    

        gen.print_spacer()
        print(gen.col('Target')+targetname)

        if not o.isdir(myms):
            print(gen.col('Measurement Set')+'not found, skipping')

        elif len(have_img) == 0:
            print(gen.col('Model')+' not found, skipping')

        else:

            steps = []        
            filename_targetname = gen.scrub_target_name(targetname)


            code = gen.get_target_code(targetname)
            if code in codes:
                code += '_'+str(ii)
                ii += 1
            codes.append(code)
        

            k_outdir = GAINTABLES+'/delaycal_'+filename_targetname+'_'+stamp+'.cc/'
            k_outname = 'delaycal_'+filename_targetname+'_'+stamp
            k_saveto = 'delaycal_'+filename_targetname+'.parmdb'


            # Target-specific kill file
            kill_file = SCRIPTS+'/kill_2GC_jobs_'+filename_targetname+'.sh'
          
            print(gen.col('Measurement Set')+myms)
            print(gen.col('Model')+data_img_prefix)
            print(gen.col('Code')+code)


            step = {}
            step['step'] = 0
            step['comment'] = 'Predict model visibilities from imaging of the DATA column'
            step['dependency'] = None
            step['id'] = 'WSDPR'+code
            step['slurm_config'] = cfg.SLURM_WSCLEAN
            step['pbs_config'] = cfg.PBS_WSCLEAN
            absmem = gen.absmem_helper(step,INFRASTRUCTURE,cfg.WSC_ABSMEM)
            syscall = CONTAINER_RUNNER+WSCLEAN_CONTAINER+' ' if USE_SINGULARITY else ''
            syscall += gen.generate_syscall_predict(msname = myms,imgbase = data_img_prefix,absmem = absmem)
            step['syscall'] = syscall
            steps.append(step)


            step = {}
            step['step'] = 1
            step['comment'] = 'Run CubiCal with f-slope solver'
            step['dependency'] = 0
            step['id'] = 'CL2GC'+code
            step['slurm_config'] = cfg.SLURM_WSCLEAN
            step['pbs_config'] = cfg.PBS_WSCLEAN
            syscall = CONTAINER_RUNNER+CUBICAL_CONTAINER+' ' if USE_SINGULARITY else ''
            syscall += gen.generate_syscall_cubical(parset = cfg.CAL_2GC_DELAYCAL_PARSET,
                    myms = myms,
                    extra_args = '--out-dir '+k_outdir+' --out-name '+k_outname+' --k-save-to '+k_saveto)
            step['syscall'] = syscall
            steps.append(step)




            target_steps.append((steps,kill_file,targetname))




    # ------------------------------------------------------------------------------
    #
    # Write the run file and kill file based on the recipe
    #
    # ------------------------------------------------------------------------------


    submit_file = 'submit_2GC_jobs.sh'

    f = open(submit_file,'w')
    f.write('#!/usr/bin/env bash\n')
    f.write('export SINGULARITY_BINDPATH='+cfg.BINDPATH+'\n')

    for content in target_steps:  
        steps = content[0]
        kill_file = content[1]
        targetname = content[2]
        id_list = []

        f.write('\n#---------------------------------------\n')
        f.write('# '+targetname)
        f.write('\n#---------------------------------------\n')

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

        if INFRASTRUCTURE != 'node':
            f.write('\n# Generate kill script for '+targetname+'\n')
        if INFRASTRUCTURE == 'idia' or INFRASTRUCTURE == 'hippo':
            kill = 'echo "scancel "$'+'" "$'.join(id_list)+' > '+kill_file+'\n'
            f.write(kill)
        elif INFRASTRUCTURE == 'chpc':
            kill = 'echo "qdel "$'+'" "$'.join(id_list)+' > '+kill_file+'\n'
            f.write(kill)

        
    f.close()

    gen.make_executable(submit_file)

    gen.print_spacer()
    print(gen.col('Run file')+submit_file)
    gen.print_spacer()

    # ------------------------------------------------------------------------------



if __name__ == "__main__":


    main()
