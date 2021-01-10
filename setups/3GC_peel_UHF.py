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
    print(gen.now()+'3GC (peeling) setup')


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


    # Get target information from project pickle

    project_info = pickle.load(open('project_info.p','rb'),encoding='latin1')

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

        if not o.isdir(myms):

            gen.print_spacer()
            print(gen.now()+'Target    | '+targetname)
            print(gen.now()+'MS        | not found, skipping')


        elif not o.isfile(cfg.CAL_3GC_PEEL_REGION):

            gen.print_spacer()
            print(gen.now()+cfg.CAL_3GC_PEEL_REGION+' not found')
            print(gen.now()+'Please provide a DS9 region file definining the source you wish to peel.')
            gen.print_spacer()
            sys.exit()

        else:

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
            outname = 'peeling_'+filename_targetname+'_'+stamp+'.cc/peeling_'+filename_targetname+'_'+stamp


            gen.print_spacer()
            print(gen.now()+'Target    | '+targetname)
            print(gen.now()+'MS        | '+myms)
            print(gen.now()+'Code      | '+code)
            print(gen.now()+'Mask      | '+mask)
            print(gen.now()+'Peeling   | '+cfg.CAL_3GC_PEEL_REGION)


            # Image prefixes
            prepeel_img_prefix = IMAGES+'/img_'+myms+'_prepeel'
            dir1_img_prefix = prepeel_img_prefix+'-'+cfg.CAL_3GC_PEEL_REGION.split('/')[-1].split('.')[0]

            # Target-specific kill file
            kill_file = SCRIPTS+'/kill_3GC_peel_jobs_'+filename_targetname+'.sh'


            step = {}
            step['step'] = 0
            step['comment'] = 'Run masked wsclean, high freq/angular resolution, on CORRECTED_DATA column of '+myms
            step['dependency'] = None
            step['id'] = 'WSDMA'+code
            step['slurm_config'] = cfg.SLURM_WSCLEAN
            step['pbs_config'] = cfg.PBS_WSCLEAN
            syscall = CONTAINER_RUNNER+WSCLEAN_CONTAINER+' ' if USE_SINGULARITY else ''
            syscall += gen.generate_syscall_wsclean(mslist=[myms],
                        imgname=prepeel_img_prefix,
                        datacol='CORRECTED_DATA',
                        briggs=cfg.CAL_3GC_PEEL_BRIGGS,
                        chanout=cfg.CAL_3GC_PEEL_NCHAN,
                        imsize=cfg.WSC_UHF_IMSIZE,
                        cellsize=cfg.WSC_UHF_CELLSIZE,
                        automask = False,
                        autothreshold = False,
                        localrms = False,
                        bda=True,
                        mask=mask)
            step['syscall'] = syscall
            steps.append(step)


            step = {}
            step['step'] = 1
            step['comment'] = 'Extract problem source defined by region into a separate set of model images'
            step['dependency'] = 0
            step['id'] = 'IMSPL'+code
            syscall = CONTAINER_RUNNER+CUBICAL_CONTAINER+' ' if USE_SINGULARITY else ''
            syscall += 'python '+OXKAT+'/3GC_split_model_images.py '
            syscall += '--region '+cfg.CAL_3GC_PEEL_REGION+' '
            syscall += '--prefix '+prepeel_img_prefix+' '
            step['syscall'] = syscall
            steps.append(step)


            step = {}
            step['step'] = 2
            step['comment'] = 'Predict problem source visibilities into MODEL_DATA column of '+myms
            step['dependency'] = 1
            step['id'] = 'WS1PR'+code
            syscall = CONTAINER_RUNNER+WSCLEAN_CONTAINER+' ' if USE_SINGULARITY else ''
            syscall += gen.generate_syscall_predict(msname=myms,imgbase=dir1_img_prefix,chanout=cfg.CAL_3GC_PEEL_NCHAN)
            step['syscall'] = syscall
            steps.append(step)


            step = {}
            step['step'] = 3
            step['comment'] = 'Add '+cfg.CAL_3GC_PEEL_DIR1COLNAME+' column to '+myms
            step['dependency'] = 2
            step['id'] = 'ADDIR'+code
            syscall = CONTAINER_RUNNER+CUBICAL_CONTAINER+' ' if USE_SINGULARITY else ''
            syscall += 'python '+TOOLS+'/add_MS_column.py '
            syscall += '--colname '+cfg.CAL_3GC_PEEL_DIR1COLNAME+' '
            syscall += myms
            step['syscall'] = syscall
            steps.append(step)


            step = {}
            step['step'] = 4
            step['comment'] = 'Copy MODEL_DATA to '+cfg.CAL_3GC_PEEL_DIR1COLNAME
            step['dependency'] = 3
            step['id'] = 'CPMOD'+code
            syscall = CONTAINER_RUNNER+CUBICAL_CONTAINER+' ' if USE_SINGULARITY else ''
            syscall += 'python '+TOOLS+'/copy_MS_column.py '
            syscall += '--fromcol MODEL_DATA '
            syscall += '--tocol '+cfg.CAL_3GC_PEEL_DIR1COLNAME+' '
            syscall += myms
            step['syscall'] = syscall
            steps.append(step)


            step = {}
            step['step'] = 5
            step['comment'] = 'Predict full sky model visibilities into MODEL_DATA column of '+myms
            step['dependency'] = 4
            step['id'] = 'WS2PR'+code
            syscall = CONTAINER_RUNNER+WSCLEAN_CONTAINER+' ' if USE_SINGULARITY else ''
            syscall += gen.generate_syscall_predict(msname=myms,imgbase=prepeel_img_prefix,chanout=cfg.CAL_3GC_PEEL_NCHAN)
            step['syscall'] = syscall
            steps.append(step)


            step = {}
            step['step'] = 6
            step['comment'] = 'Run CubiCal to solve for G (full model) and dE (problem source), peel out problem source'
            step['dependency'] = 5
            step['id'] = 'CL3GC'+code
            step['slurm_config'] = cfg.SLURM_WSCLEAN
            step['pbs_config'] = cfg.PBS_WSCLEAN
            syscall = CONTAINER_RUNNER+CUBICAL_CONTAINER+' ' if USE_SINGULARITY else ''
            syscall += gen.generate_syscall_cubical(parset=cfg.CAL_3GC_PEEL_PARSET,myms=myms,outname=outname)
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
    print(gen.now()+'Created '+submit_file)
    gen.print_spacer()

    # ------------------------------------------------------------------------------



if __name__ == "__main__":


    main()
