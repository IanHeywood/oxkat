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
    print(gen.col()+'3GC (peeling) setup')
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
    TOOLS = cfg.TOOLS

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
    WSCLEAN_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.WSCLEAN_PATTERN,USE_SINGULARITY)


    # Get target information from project info json file

    with open('project_info.json') as f:
        project_info = json.load(f)

    target_ids = project_info['target_ids'] 
    target_names = project_info['target_names']
    target_ms = project_info['target_ms']


    # ------------------------------------------------------------------------------
    #
    # 3GC peeling recipe definition
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
        CAL_3GC_PEEL_REGION = cfg.CAL_3GC_PEEL_REGION
        skip = False

        if not o.isdir(myms):
            gen.print_spacer()
            print(gen.col('Target')+targetname)
            print(gen.col('MS')+'not found, skipping')
            skip = True

        if CAL_3GC_PEEL_REGION == '':
            region = glob.glob('*'+targetname+'*peel*.reg')
            if len(region) == 0:
                CAL_3GC_PEEL_REGION = ''
            else:
                CAL_3GC_PEEL_REGION = region[0]

        if not o.isfile(CAL_3GC_PEEL_REGION):
            gen.print_spacer()
            print(gen.col('Target')+targetname)
            print(gen.col('Measurement Set')+myms)
            print(gen.col()+'Please provide a DS9 region file definining the source you wish to peel.')
            print(gen.col()+'This can be specified in the config or by placing a file of the form:')
            print(gen.col()+'       *'+targetname+'*peel*.reg')
            print(gen.col()+'in this folder. Skipping.')
            skip = True

        if not skip:

            steps = []        
            filename_targetname = gen.scrub_target_name(targetname)


            code = gen.get_target_code(targetname)
            if code in codes:
                code += '_'+str(ii)
                ii += 1
            codes.append(code)
        

            # Look for the FITS mask for this target
            mask1 = sorted(glob.glob(IMAGES+'/*'+filename_targetname+'*.mask1.fits'))
            if len(mask1) > 0:
                mask = mask1[0]
            else:
                mask = 'auto'


            # Generate output dir for CubiCal
            outdir = GAINTABLES+'/peeling_'+filename_targetname+'_'+stamp+'.cc/'
            outname = 'peeling_'+filename_targetname+'_'+stamp


            gen.print_spacer()
            print(gen.col('Target')+targetname)
            print(gen.col('Measurement Set')+myms)
            print(gen.col('Code')+code)
            print(gen.col('Mask')+mask)
            print(gen.col('Peeling region')+CAL_3GC_PEEL_REGION)


            # Image prefixes
            prepeel_img_prefix = IMAGES+'/img_'+myms+'_prepeel'
            dir1_img_prefix = prepeel_img_prefix+'-'+CAL_3GC_PEEL_REGION.split('/')[-1].split('.')[0]

            # Target-specific kill file
            kill_file = SCRIPTS+'/kill_3GC_peel_jobs_'+filename_targetname+'.sh'


            step = {}
            step['step'] = 0
            step['comment'] = 'Run masked wsclean, high freq/angular resolution, on CORRECTED_DATA column of '+myms
            step['dependency'] = None
            step['id'] = 'WSDMA'+code
            step['slurm_config'] = cfg.SLURM_EXTRALONG
            step['pbs_config'] = cfg.PBS_EXTRALONG
            absmem = gen.absmem_helper(step,INFRASTRUCTURE,cfg.WSC_ABSMEM)
            syscall = CONTAINER_RUNNER+WSCLEAN_CONTAINER+' ' if USE_SINGULARITY else ''
            syscall += gen.generate_syscall_wsclean(mslist = [myms],
                        imgname = prepeel_img_prefix,
                        datacol = 'CORRECTED_DATA',
                        briggs = cfg.CAL_3GC_PEEL_BRIGGS,
                        chanout = cfg.CAL_3GC_PEEL_NCHAN,
                        automask = False,
                        autothreshold = False,
                        localrms = False,
                        nomodel = True,
                        mask = mask,
                        absmem = absmem)
            step['syscall'] = syscall
            steps.append(step)


            step = {}
            step['step'] = 1
            step['comment'] = 'Fix any NaN values in blanked wsclean sub-band models'
            step['dependency'] = 0
            step['id'] = 'FXNAN'+code
            syscall = CONTAINER_RUNNER+CUBICAL_CONTAINER+' ' if USE_SINGULARITY else ''
            syscall += 'python3 '+TOOLS+'/fix_nan_models.py '+prepeel_img_prefix+'-0'
            step['syscall'] = syscall
            steps.append(step)


            step = {}
            step['step'] = 2
            step['comment'] = 'Extract problem source defined by region into a separate set of model images'
            step['dependency'] = 1
            step['id'] = 'IMSPL'+code
            syscall = CONTAINER_RUNNER+CUBICAL_CONTAINER+' ' if USE_SINGULARITY else ''
            syscall += 'python3 '+OXKAT+'/3GC_split_model_images.py '
            syscall += '--region '+CAL_3GC_PEEL_REGION+' '
            syscall += '--prefix '+prepeel_img_prefix+' '
            step['syscall'] = syscall
            steps.append(step)


            step = {}
            step['step'] = 3
            step['comment'] = 'Predict problem source visibilities into MODEL_DATA column of '+myms
            step['dependency'] = 2
            step['id'] = 'WS1PR'+code
            step['slurm_config'] = cfg.SLURM_WSCLEAN
            step['pbs_config'] = cfg.PBS_WSCLEAN
            absmem = gen.absmem_helper(step,INFRASTRUCTURE,cfg.WSC_ABSMEM)
            syscall = CONTAINER_RUNNER+WSCLEAN_CONTAINER+' ' if USE_SINGULARITY else ''
            syscall += gen.generate_syscall_predict(msname = myms, imgbase = dir1_img_prefix, chanout = cfg.CAL_3GC_PEEL_NCHAN, absmem = absmem)
            step['syscall'] = syscall
            steps.append(step)


            step = {}
            step['step'] = 4
            step['comment'] = 'Add '+cfg.CAL_3GC_PEEL_DIR1COLNAME+' column to '+myms
            step['dependency'] = 3
            step['id'] = 'ADDIR'+code
            syscall = CONTAINER_RUNNER+CUBICAL_CONTAINER+' ' if USE_SINGULARITY else ''
            syscall += 'python3 '+TOOLS+'/add_MS_column.py '
            syscall += '--colname '+cfg.CAL_3GC_PEEL_DIR1COLNAME+' '
            syscall += myms
            step['syscall'] = syscall
            steps.append(step)


            step = {}
            step['step'] = 5
            step['comment'] = 'Copy MODEL_DATA to '+cfg.CAL_3GC_PEEL_DIR1COLNAME
            step['dependency'] = 4
            step['id'] = 'CPMOD'+code
            syscall = CONTAINER_RUNNER+CUBICAL_CONTAINER+' ' if USE_SINGULARITY else ''
            syscall += 'python3 '+TOOLS+'/copy_MS_column.py '
            syscall += '--fromcol MODEL_DATA '
            syscall += '--tocol '+cfg.CAL_3GC_PEEL_DIR1COLNAME+' '
            syscall += myms
            step['syscall'] = syscall
            steps.append(step)


            step = {}
            step['step'] = 6
            step['comment'] = 'Predict full sky model visibilities into MODEL_DATA column of '+myms
            step['dependency'] = 5
            step['id'] = 'WS2PR'+code
            step['slurm_config'] = cfg.SLURM_WSCLEAN
            step['pbs_config'] = cfg.PBS_WSCLEAN
            absmem = gen.absmem_helper(step,INFRASTRUCTURE,cfg.WSC_ABSMEM)
            syscall = CONTAINER_RUNNER+WSCLEAN_CONTAINER+' ' if USE_SINGULARITY else ''
            syscall += gen.generate_syscall_predict(msname = myms, imgbase = prepeel_img_prefix, chanout = cfg.CAL_3GC_PEEL_NCHAN, absmem = absmem)
            step['syscall'] = syscall
            steps.append(step)


            step = {}
            step['step'] = 7
            step['comment'] = 'Copy CORRECTED_DATA to DATA'
            step['dependency'] = 6
            step['id'] = 'CPCOR'+code
            syscall = CONTAINER_RUNNER+CUBICAL_CONTAINER+' ' if USE_SINGULARITY else ''
            syscall += 'python3 '+TOOLS+'/copy_MS_column.py '
            syscall += '--fromcol CORRECTED_DATA '
            syscall += '--tocol DATA '
            syscall += myms
            step['syscall'] = syscall
            steps.append(step)


            step = {}
            step['step'] = 8
            step['comment'] = 'Run CubiCal to solve for G (full model) and dE (problem source), peel out problem source'
            step['dependency'] = 7
            step['id'] = 'CL3GC'+code
            step['slurm_config'] = cfg.SLURM_WSCLEAN
            step['pbs_config'] = cfg.PBS_WSCLEAN
            syscall = CONTAINER_RUNNER+CUBICAL_CONTAINER+' ' if USE_SINGULARITY else ''
            syscall += gen.generate_syscall_cubical(parset=cfg.CAL_3GC_PEEL_PARSET, myms=myms, extra_args='--out-name '+outname+' --out-dir '+outdir)
            step['syscall'] = syscall
            steps.append(step)

    
            target_steps.append((steps,kill_file,targetname))


    # ------------------------------------------------------------------------------
    #
    # Write the run file and kill file based on the recipe
    #
    # ------------------------------------------------------------------------------


    submit_file = 'submit_3GC_peel_jobs.sh'

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
