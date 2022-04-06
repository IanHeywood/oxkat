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
    print(gen.col()+'3GC (facet-based corrections) setup')
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

    if INFRASTRUCTURE == 'idia':
        myNCPU = 12  # Dial back the parallelism for IDIA nodes
    elif INFRASTRUCTURE == 'chpc':
        myNCPU = 23 # Kind of meaningless as this stuff probably won't ever run on CHPC
    else:
        myNCPU = 40 # Assumed NCPU for standalone nodes
    
    if CONTAINER_PATH is not None:
        CONTAINER_RUNNER='singularity exec '
    else:
        CONTAINER_RUNNER=''


    DDFACET_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.DDFACET_PATTERN,USE_SINGULARITY) 
    KILLMS_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.KILLMS_PATTERN,USE_SINGULARITY)


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
        

            # Look for the zoomed FITS mask for this target
            mask1 = sorted(glob.glob(IMAGES+'/*'+filename_targetname+'*.mask1.zoom*.fits'))
            if len(mask1) > 0:
                mask = mask1[0]
            else:
                mask = 'auto'


            gen.print_spacer()
            print(gen.col('Target')+targetname)
            print(gen.col('Measurement Set')+myms)
            print(gen.col('Code')+code)
            print(gen.col('Mask')+mask)


            # Image prefixes 
            ddf_img_prefix = IMAGES+'/img_'+myms+'_DDFpcal'
            kms_img_prefix = IMAGES+'/img_'+myms+'_DDFkMS'

            # Target-specific kill file
            kill_file = SCRIPTS+'/kill_3GC_facet_jobs_'+filename_targetname+'.sh'


            step = {}
            step['step'] = 0
            step['comment'] = 'Run DDFacet, masked deconvolution of CORRECTED_DATA column of '+myms
            step['dependency'] = None
            step['id'] = 'DDCMA'+code
            step['slurm_config'] = cfg.SLURM_HIGHMEM
            step['pbs_config'] = cfg.PBS_WSCLEAN
            syscall = CONTAINER_RUNNER+DDFACET_CONTAINER+' ' if USE_SINGULARITY else ''
            syscall += gen.generate_syscall_ddfacet(mspattern=myms,
                        imgname=ddf_img_prefix,
                        ncpu=myNCPU,
                        mask=mask,
                        sparsification='5,3,2')
            step['syscall'] = syscall
            steps.append(step)


            step = {}
            step['step'] = 1
            step['comment'] = 'Run PyBDSF on the restored DDFacet image to get a source catalogue for clustering'
            step['dependency'] = 0
            step['id'] = 'BDSF_'+code
            pybdsf_call, pybdsf_catalogue = gen.generate_syscall_pybdsf(ddf_img_prefix+'.app.restored.fits')
            syscall = CONTAINER_RUNNER+DDFACET_CONTAINER+' ' if USE_SINGULARITY else ''
            syscall += pybdsf_call
            step['syscall'] = syscall
            steps.append(step)


            step = {}
            step['step'] = 2
            step['comment'] = 'Run ClusterCat on the PyBDSF catalogue to chunk up the sky model'
            step['dependency'] = 1
            step['id'] = 'CCAT_'+code
            ccat_call, ccat_file = gen.generate_syscall_clustercat(pybdsf_catalogue)
            syscall = CONTAINER_RUNNER+DDFACET_CONTAINER+' ' if USE_SINGULARITY else ''
            syscall += ccat_call
            step['syscall'] = syscall
            steps.append(step)


            step = {}
            step['step'] = 3
            step['comment'] = 'Run killMS'
            step['dependency'] = 2
            step['id'] = 'KILMS'+code
            step['slurm_config'] = cfg.SLURM_HIGHMEM
            step['pbs_config'] = cfg.PBS_WSCLEAN
            syscall = CONTAINER_RUNNER+KILLMS_CONTAINER+' ' if USE_SINGULARITY else ''
            syscall += gen.generate_syscall_killms(myms=myms,
                        baseimg=ddf_img_prefix,
                        ncpu=myNCPU,
                        outsols='killms-cohjones',
                        nodesfile=ccat_file)
            step['syscall'] = syscall
            steps.append(step)


            step = {}
            step['step'] = 4
            step['comment'] = 'Run DDFacet on CORRECTED_DATA of '+myms+', applying killMS solutions'
            step['dependency'] = 3
            step['id'] = 'DDKMA'+code
            step['slurm_config'] = cfg.SLURM_HIGHMEM
            step['pbs_config'] = cfg.PBS_WSCLEAN
            syscall = CONTAINER_RUNNER+DDFACET_CONTAINER+' ' if USE_SINGULARITY else ''
            syscall += gen.generate_syscall_ddfacet(mspattern=myms,
                        imgname=kms_img_prefix,
                        chunkhours=1,
                        ncpu=myNCPU,
                        initdicomodel=ddf_img_prefix+'.DicoModel',
                        hogbom_maxmajoriter=0,
                        hogbom_maxminoriter=1000,
                        mask=mask,
                        ddsols='killms-cohjones')
            step['syscall'] = syscall
            steps.append(step)


            target_steps.append((steps,kill_file,targetname))




    # ------------------------------------------------------------------------------
    #
    # Write the run file and kill file based on the recipe
    #
    # ------------------------------------------------------------------------------


    submit_file = 'submit_3GC_facet_jobs.sh'

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
