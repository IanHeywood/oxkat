#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import glob
import os.path as o
import pickle
import sys
sys.path.append(o.abspath(o.join(o.dirname(sys.modules[__name__].__file__), "..")))


from oxkat import generate_jobs as gen


def main():


    CWD = gen.CWD
    OXKAT = gen.OXKAT
    PARSETS = gen.PARSETS
    SCRIPTS = gen.SCRIPTS
    LOGS = gen.LOGS
 

    submit_file = 'run_1GC_jobs.sh'


    gen.setup_dir(SCRIPTS)
    gen.setup_dir(LOGS)


    f = open(submit_file,'w')


    myms = glob.glob('*.ms')[0]
    code = gen.get_code(myms)
    myms = myms.replace('.ms','_wtspec.ms')

    syscall = 'casa -c '+OXKAT+'/casa_average_to_1k_add_wtspec.py --nologger --log2term --nogui\n'


    f.write(syscall+'\n')


    syscall = 'python '+OXKAT+'/00_setup.py '+myms+'\n'


    f.write(syscall+'\n')


    script_list = ['casa_basic_flags.py',
        'casa_split_calibrators.py',
        'casa_flag_calibrator_ms.py',
        'casa_get_secondary_model.py',
        'casa_tfcrop_cals_data.py',
        'casa_1GC_using_secondary_model.py',
        'casa_tfcrop_targets_corrected.py']

    for script in script_list:
        syscall = 'casa -c '+OXKAT+'/'+script+' --nologger --log2term --nogui\n'

        f.write(syscall+'\n')


    f.close()


if __name__ == "__main__":


    main()