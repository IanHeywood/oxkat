# oxkat

![](https://i.imgur.com/pVP4edt.jpg)

A lightweight set of scripts for processing MeerKAT data.

"Ceci n'est pas une pipe[line]" (_The Treachery of Images_, René Magritte, 1929)

---

This 'chpc' branch is under development.

Major changes:

* Default settings which were buried all over the place are being gathered in one place in the `oxkat/config.py` file.

* Containers are identified via pattern matching inside a specified path (also set in the `config.py` file).

* Slurm script generation has been replaced by the `job_handler` function in `generate_jobs.py` which also handles filename generation. This makes the scripts in `setups` a lot leaner and simpler.

* `setups/1GC.py` now takes a command line argument, one of `idia`, `chpc` or `node` to specify where you are running it. Relevant scripts and runfiles will be generated accordingly.

---

Example for usage on the CHPC lengau cluster:

0. You cannot build containers on lengau yourself, so you will have to copy them in via the CHPC's `scp.chpc.ac.za` server. You will also (obviously) have to get your MeerKAT data onto the `/lustre` filesystem.

1. Log into lengau:

```
$ ssh iheywood@lengau.chpc.ac.za
```

2. Clone this repo somewhere:

```
$ cd ~/Software
$ git clone -b chpc https://github.com/IanHeywood/oxkat.git
```

3. Go to your scratch data area containing your pristine MS (this will not be modified at all):

```
$ cd /home/iheywood/lustre/GC/GC29
```

4. Make a symlink to the scripts:

```
$ ln -s ~/Software/oxkat/* .
```

5. Setup and submit the 1GC jobs:

```
$ python setups/1GC.py chpc
$ source submit_1GC_jobs.sh
```

...
..
.

---

Example for usage on the IDIA slurm cluster:

1. Log in to the slurm head node:

```
$ ssh ianh@slurm.ilifu.ac.za
```

2. Clone this repo somewhere:

```
$ cd ~/Software
$ git clone https://github.com/IanHeywood/oxkat.git
```

3. Go to a scratch data area:

```
$ cd /scratch/users/ianh/XMM12
```

4. Make a symlink to the scripts and the data you want to process:

```
$ ln -s ~/Software/oxkat/* .
$ ln -s /idia/projects/mightee/1538856059/1538856059_sdp_l0.full_1284.full_pol.ms .
```

5. Set up and submit the 1GC jobs:

```
$ python setups/1GC.py idia
$ source submit_1GC_jobs.sh
```

6. If something goes wrong you can subsequently kill the jobs using:

```
$ source kill_1GC_jobs.sh
```

7. If that completes successfully you can set up and submit the 2GC jobs, which does imaging with an iteration of phase-only self-cal:

```
$ python setups/2GC.py
$ source submit_2GC_jobs.sh
```

8. Again, you can kill the 2GC jobs using:

```
$ source kill_2GC_jobs.sh
```

The setup scripts will also produce a `run_*GC_jobs.sh` for use on standalone servers. 

---

Notes:

* You might not have permission to use the containers that I store in my home area, in which case you'll have to pull your own. [@SpheMakh](https://github.com/sphemakh)'s [stimela](https://hub.docker.com/u/stimela) repo is a life saver here. You can build the usual suspects with [`tools/pull_containers.sh`](https://github.com/IanHeywood/oxkat/blob/master/tools/pull_containers.sh), and then you'll just have to edit [line 26](https://github.com/IanHeywood/oxkat/blob/master/oxkat/generate_jobs.py#L26) in [`oxkat/generate_jobs.py`](https://github.com/IanHeywood/oxkat/blob/master/oxkat/generate_jobs.py) to reflect wherever it is you've built them.

* Joint imaging and self-calibration of multiple epochs is not yet automated.

* This repo is just a place for me to keep my scripts. I hope you find it useful but please don't mail me if your data vanishes or your computer melts. 

* Please file bugs, questions, comments as issues on this page.

Thanks.
