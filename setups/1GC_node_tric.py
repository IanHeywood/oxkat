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
    CASA_CONTAINER = gen.XCASA_CONTAINER
    CUBICAL_CONTAINER = gen.XCUBICAL_CONTAINER
    TRICOLOUR_CONTAINER = gen.XTRICOLOUR_CONTAINER

    CASA_EXEC = gen.XCASA_EXEC
 

    submit_file = 'run_1GC_jobs.sh'


    gen.setup_dir(SCRIPTS)
    gen.setup_dir(LOGS)


    f = open(submit_file,'w')


    myms = glob.glob('*.ms')[0]
    code = gen.get_code(myms)
    myms = myms.replace('.ms','_wtspec.ms')


    # ------------------------------------------------------------------------------
    # Average MS to 1k channels and add weight spectrum column


    syscall = CASA_EXEC+' -c '+OXKAT+'/casa_average_to_1k_add_wtspec.py --nologger --log2term --nogui'


    f.write(syscall+'\n')


    # ------------------------------------------------------------------------------
    # Run setup script


    syscall='python '+OXKAT+'/00_setup.py '+myms

    f.write('singularity exec '+CUBICAL_CONTAINER+' '+syscall+'\n')


    # ------------------------------------------------------------------------------
    # Run basic flags


    syscall = CASA_EXEC+' -c '+OXKAT+'/casa_basic_flags.py --nologger --log2term --nogui'


    f.write(syscall+'\n')


    # ------------------------------------------------------------------------------
    # Autoflagger on calibrators 1


    runfile = SCRIPTS+'/run_tricolour_1.sh'


    syscall = 'singularity exec '+CUBICAL_CONTAINER+' '
    syscall += gen.generate_syscall_tricolour(myms=myms,config='',datacol='DATA',fields='cals',fs='polarisation',runfile=runfile)+'\n'
    syscall += 'singularity exec '+TRICOLOUR_CONTAINER+' '+runfile


    f.write(syscall+'\n')


    # ------------------------------------------------------------------------------
    # Reference calibration cals only


    syscall = CASA_EXEC+' -c '+OXKAT+'/casa_reference_cal_calzone.py --nologger --log2term --nogui'


    f.write(syscall+'\n')


    # ------------------------------------------------------------------------------
    # Autoflagger on calibrators 2


    runfile = SCRIPTS+'/run_tricolour_2.sh'


    syscall = 'singularity exec '+CUBICAL_CONTAINER+' '
    syscall += gen.generate_syscall_tricolour(myms=myms,config='',datacol='DATA',fields='cals',fs='polarisation',runfile=runfile)+'\n'
    syscall += 'singularity exec '+TRICOLOUR_CONTAINER+' '+runfile


    f.write(syscall+'\n')


    # ------------------------------------------------------------------------------
    # Full reference calibration 


    syscall = CASA_EXEC+' -c '+OXKAT+'/casa_reference_cal_full.py --nologger --log2term --nogui'


    f.write(syscall+'\n')


    # ------------------------------------------------------------------------------
    # Autoflagger on targets


    runfile = SCRIPTS+'/run_tricolour_3.sh'


    syscall = 'singularity exec '+CUBICAL_CONTAINER+' '
    syscall += gen.generate_syscall_tricolour(myms=myms,config='',datacol='DATA',fields='all',fs='polarisation',runfile=runfile)+'\n'
    syscall += 'singularity exec '+TRICOLOUR_CONTAINER+' '+runfile


    f.write(syscall+'\n')



    # ------------------------------------------------------------------------------
    # Split targets


    syscall = CASA_EXEC+' -c '+OXKAT+'/casa_split_targets.py --nologger --log2term --nogui'


    f.write(syscall+'\n')


    # ------------------------------------------------------------------------------


    f.close()


if __name__ == "__main__":


    main()