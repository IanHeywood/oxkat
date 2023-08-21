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
    print(gen.col()+'2GC (direction independent selfcal) setup')
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


    CASA_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.CASA_PATTERN,USE_SINGULARITY)
    MAKEMASK_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.MAKEMASK_PATTERN,USE_SINGULARITY)
    RAGAVI_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.RAGAVI_PATTERN,USE_SINGULARITY)
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

    # Loop over targets

    for tt in range(0,len(target_ids)):

        targetname = target_names[tt]
        myms = target_ms[tt]

        if not o.isdir(myms):

            gen.print_spacer()
            print(gen.col('Target')+targetname)
            print(gen.col('MS')+'not found, skipping')

        else:

            steps = []        
            filename_targetname = gen.scrub_target_name(targetname)


            code = gen.get_target_code(targetname)
            if code in codes:
                code += '_'+str(ii)
                ii += 1
            codes.append(code)
        

            # Look for the FITS mask for this target
            mask0 = sorted(glob.glob(IMAGES+'/*'+filename_targetname+'*.mask0.fits'))
            if len(mask0) > 0:
                mask = mask0[0]
            else:
                mask = 'auto'


            gen.print_spacer()
            print(gen.col('Target')+targetname)
            print(gen.col('Measurement Set')+myms)
            print(gen.col('Code')+code)
            print(gen.col('Mask')+mask)


            # Image prefixes
            data_img_prefix = IMAGES+'/img_'+myms+'_datamask'
            corr_img_prefix = IMAGES+'/img_'+myms+'_pcalmask'

            # Target-specific kill file
            kill_file = SCRIPTS+'/kill_2GC_jobs_'+filename_targetname+'.sh'


            step = {}
            step['step'] = 0
            step['comment'] = 'Run wsclean, masked deconvolution of the DATA column of '+myms
            step['dependency'] = None
            step['id'] = 'WSDMA'+code
            step['slurm_config'] = cfg.SLURM_WSCLEAN
            step['pbs_config'] = cfg.PBS_WSCLEAN
            absmem = gen.absmem_helper(step,INFRASTRUCTURE,cfg.WSC_ABSMEM)
            syscall = CONTAINER_RUNNER+WSCLEAN_CONTAINER+' ' if USE_SINGULARITY else ''
            syscall += gen.generate_syscall_wsclean(mslist=[myms],
                        imgname = data_img_prefix,
                        datacol = 'DATA',
                        bda = True,
                        automask = False,
                        autothreshold = False,
                        localrms = False,
                        mask = mask,
                        absmem = absmem)
            step['syscall'] = syscall
            steps.append(step)


            step = {}
            step['step'] = 1
            step['comment'] = 'Predict model visibilities from imaging of the DATA column'
            step['dependency'] = 0
            step['id'] = 'WSDPR'+code
            step['slurm_config'] = cfg.SLURM_WSCLEAN
            step['pbs_config'] = cfg.PBS_WSCLEAN
            absmem = gen.absmem_helper(step,INFRASTRUCTURE,cfg.WSC_ABSMEM)
            syscall = CONTAINER_RUNNER+WSCLEAN_CONTAINER+' ' if USE_SINGULARITY else ''
            syscall += gen.generate_syscall_predict(msname = myms, imgbase = data_img_prefix, absmem = absmem)
            step['syscall'] = syscall
            steps.append(step)


            step = {}
            step['step'] = 2
            step['comment'] = 'Run CASA self-calibration script'
            step['dependency'] = 1
            step['id'] = 'CL2GC'+code
            syscall = CONTAINER_RUNNER+CASA_CONTAINER+' ' if USE_SINGULARITY else ''
            syscall += gen.generate_syscall_casa(casascript=OXKAT+'/2GC_casa_selfcal_target_amp_phases.py',
                        extra_args='mslist='+myms)
            step['syscall'] = syscall
            steps.append(step)


            step = {}
            step['step'] = 3
            step['comment'] = 'Plot the self-calibration gain solutions'
            step['dependency'] = 2
            step['id'] = 'PLTAB'+code
            syscall = CONTAINER_RUNNER+RAGAVI_CONTAINER+' ' if USE_SINGULARITY else ''
            syscall += 'python3 '+OXKAT+'/PLOT_gaintables.py cal_2GC_*'+myms+'*'
            step['syscall'] = syscall
            steps.append(step)


            step = {}
            step['step'] = 4
            step['comment'] = 'Run wsclean, masked deconvolution of the CORRECTED_DATA column of '+myms
            step['dependency'] = 2
            step['id'] = 'WSCMA'+code
            step['slurm_config'] = cfg.SLURM_WSCLEAN
            step['pbs_config'] = cfg.PBS_WSCLEAN
            absmem = gen.absmem_helper(step,INFRASTRUCTURE,cfg.WSC_ABSMEM)
            syscall = CONTAINER_RUNNER+WSCLEAN_CONTAINER+' ' if USE_SINGULARITY else ''
            syscall += gen.generate_syscall_wsclean(mslist = [myms],
                        imgname = corr_img_prefix,
                        datacol = 'CORRECTED_DATA',
                        bda = True,
                        automask = False,
                        autothreshold = False,
                        localrms = False,
                        mask = mask,
                        absmem = absmem)
            step['syscall'] = syscall
            steps.append(step)


            step = {}
            step['step'] = 5
            step['comment'] = 'Refine the cleaning mask for '+targetname+', crop for use with DDFacet'
            step['dependency'] = 4
            step['id'] = 'MASK1'+code
            syscall = CONTAINER_RUNNER+MAKEMASK_CONTAINER+' ' if USE_SINGULARITY else ''
            syscall += gen.generate_syscall_makemask(restoredimage = corr_img_prefix+'-MFS-image.fits',
                                    outfile = corr_img_prefix+'-MFS-image.mask1.fits',
                                    thresh = 5.5,
                                    zoompix = cfg.DDF_NPIX)[0]
            step['syscall'] = syscall
            steps.append(step)


            step = {}
            step['step'] = 6
            step['comment'] = 'Predict model visibilities from imaging of the CORRECTED_DATA column'
            step['dependency'] = 4
            step['id'] = 'WSCPR'+code
            step['slurm_config'] = cfg.SLURM_WSCLEAN
            step['pbs_config'] = cfg.PBS_WSCLEAN
            absmem = gen.absmem_helper(step,INFRASTRUCTURE,cfg.WSC_ABSMEM)
            syscall = CONTAINER_RUNNER+WSCLEAN_CONTAINER+' ' if USE_SINGULARITY else ''
            syscall += gen.generate_syscall_predict(msname = myms, imgbase = corr_img_prefix, absmem = absmem)
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
