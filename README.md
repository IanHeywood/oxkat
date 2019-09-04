# oxkat

![](https://i.imgur.com/pVP4edt.jpg)

A lightweight set of scripts for processing MeerKAT data.

"Ceci n'est pas une pipe[line]" (_The Treachery of Images_, René Magritte, 1929)

---

Example for usage on the IDIA slurm cluster:

1. Log in to the slurm head node:

```
$ssh ianh@slurm.ilifu.ac.za`
```

2. Clone this repo somewhere:

```
$ cd ~/Software
$ git clone https://github.com/IanHeywood/oxkat.git
```

3. Go to a scratch data area:

```
$ cd /scratch/users/ianh/XMM12`
```

4. Make a symlink to the scripts and the data you want to process:

```
$ ln -s ~/Software/oxkat/* .
$ ln -s /idia/projects/mightee/1538856059/1538856059_sdp_l0.full_1284.full_pol.ms .
```

5. Set up and submit the 1GC jobs:

```
$ python setups/1GC_slurm.py
$ source submit_1GC_jobs.sh
```

6. If something goes wrong you can subsequently kill the jobs using:

```
$ source kill_1GC_jobs.sh
```

7. If that completes successfully you can set up and submit the 2GC jobs, which does an imaging with an iteration of phase-only self-cal:

```
$ python setups/2GC_slurm.py
$ source submit_2GC_jobs.sh
```

Note that CubiCal currently does not run on the IDIA slurm worker nodes, so a temporary alternative 2GC script using CASA's `gaincal` task is:

```
$ python waterhole/2GC_slurm_CASA-selfcal.py
$ source submit_2GC_jobs.sh
```

8. Again, you can kill the 2GC jobs using:

```
$ source kill_2GC_jobs.sh
```
