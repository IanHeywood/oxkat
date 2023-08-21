![](https://i.imgur.com/u3bvu9n.png)
# oxkat

<b>"Ceci n'est pas une pipe[line]"</b><br> 
_The Treachery of Images_, René Magritte, 1929

---

* [What is this?](README.md#what-is-this)
* [Quick start](README.md#quick-start)
* [Containers](README.md#containers)
* [Software roll-call](README.md#software-package-roll-call)

---

## What is this?


* A set of `Python` scripts with the aim of (semi-)automatically processing [MeerKAT](https://www.sarao.ac.za/science-engineering/meerkat/) data. 


* At the core is a set of functions that generate calls to [various pieces](README.md#software-package-roll-call) of radio astronomy software, a semi-modular bunch of CASA scripts for performing reference calibration, and a [fairly sizeable list](oxkat/config.py) of default parameters. The defaults at present cater for full-band Stokes-I continuum imaging, including the correction of direction-dependent effects.


* Job script generation and dependency chains are automatically handled when running on the [ilifu/IDIA](https://www.idia.ac.za/) cluster, UKZN's [hippo](https://astro.ukzn.ac.za/~hippo/) cluster, or the [CHPC](https://www.chpc.ac.za/)'s [Lengau](https://www.chpc.ac.za/index.php/resources/lengau-cluster) cluster.


* Setup scripts glue the above components together into a processing recipe. The default procedure is broken down into stages, after each of which it is advisable to pause and examine the state of the process before continuing.  


* The intention is that the bar to entry is low. If you have stock `Python` then nothing else needs installing apart from [`Singularity`](https://github.com/hpcng/singularity), which is available on both the ilifu/IDIA and CHPC clusters. All the underlying radio astronomy packages are containerised. The `Singularity` layer can also be disabled for running installations on your own machine, either directly, or inside a Python virtual environment.


* If you publish results that have made use of `oxkat` then [please cite the ACSL entry](https://ui.adsabs.harvard.edu/abs/2020ascl.soft09003H/abstract), and (more importantly) the [underlying packages](README.md#software-package-roll-call) used.


* Please file bugs, suggestions, questions, etc. as [issues](https://github.com/IanHeywood/oxkat/issues).


---

## Quick start

1. Once you have the [container(s) in place](README.md#containers) then log into your machine or cluster, e.g.:

   ```
   $ ssh ianh@slurm.ilifu.ac.za
   ```

2. Navigate to a working area / scratch space:

   ```
   $ cd /scratch/users/ianh/XMM12
   ```

3. Clone the root contents of this repo into it:

   ```
   $ git clone https://github.com/IanHeywood/oxkat.git .
   ```

4. Make a symlink to your MeerKAT Measurement Set (or place it in the working folder, it will not be modified at all):

   ```
   $ ln -s /idia/projects/mightee/1538856059/1538856059_sdp_l0.full_1284.full_pol.ms .
   ```

5. The first step is to run a script that gathers some required information about the observation:

   ```
   $ python setups/0_GET_INFO.py idia
   $ ./submit_info_job.sh
   ```

6. Once this is complete you can generate and submit the jobs required for the reference calibration (1GC):

   ```
   $ python setups/1GC.py idia
   $ ./submit_1GC_jobs.sh
   ```

7. If something goes wrong you can kill the running and queued jobs on a cluster with:

   ```
   $ source SCRIPTS/kill_1GC_jobs.sh
   ```

8. Once all the jobs have completed then you can examine the products, and move on to the setup for the next steps in the same fashion. 

Please see the [setups README](setups/README.md) for more details about the general workflow. Most of the settings can be tuned via the [`config.py`](oxkat/config.py) file.

---

## Containers

There is a dedicated `Singularity` container (`oxkat-0.41.sif`) available that contains all the necessary packages and dependencies. This is available in the general container repository on the ilifu/IDIA cluster, and the default settings should pick it up automatically when that cluster is being used. For other systems the container will have to be downloaded (or copied over). The container can be downloaded [here](https://entangled.physics.ox.ac.uk/index.php/s/jmHRBQyyB6Zm2fj). 

String patterns for package-specific containers are specified in the [`config.py`](oxkat/config.py) file. The scripts will search for containers that match these patterns in the container paths, so it's simple to swap a particular package out for a different version as long as you have it containerised.

---

## Software package roll-call


| Package | Stage | Purpose | Reference |
| --- | --- | --- | --- | 
| [`astropy`](https://www.astropy.org/) | 1GC, 3GC | Coordinates, time standards, FITS file manipulation | [Astropy Collaboration, 2013](https://ui.adsabs.harvard.edu/abs/2013A%26A...558A..33A/abstract), [Astropy Collaboration, 2018](https://ui.adsabs.harvard.edu/abs/2018AJ....156..123A/abstract)|
| [`CASA`](https://casa.nrao.edu/) | 1GC | Averaging, splitting, cross calibration, DI self-calibration, flagging | [McMullin et al., 2007](https://ui.adsabs.harvard.edu/abs/2007ASPC..376..127M/abstract)|
| [`CubiCal`](https://github.com/ratt-ru/CubiCal) | 2GC, 3GC | DI / DD self-calibration | [Kenyon et al., 2018](https://ui.adsabs.harvard.edu/abs/2018MNRAS.478.2399K/abstract)|
| [`DDFacet`](https://github.com/saopicc/DDFacet) | 3GC | Imaging with direction-dependent corrections | [Tasse et al., 2018](https://ui.adsabs.harvard.edu/abs/2018A%26A...611A..87T/abstract) | 
| [`killMS`](https://github.com/saopicc/killMS) | 3GC | DD self-calibration| [Tasse, 2014](https://ui.adsabs.harvard.edu/abs/2014A%26A...566A.127T/abstract); [Smirnov & Tasse, 2014](https://ui.adsabs.harvard.edu/abs/2015MNRAS.449.2668S/abstract) |
| [`owlcat`](https://github.com/ska-sa/owlcat/) | 2GC, 3GC | FITS file manipulation | - |
| [`ragavi`](https://github.com/ratt-ru/ragavi/) | 1GC, 2GC | Plotting gain solutions | - |
| [`shadeMS`](https://github.com/ratt-ru/shadeMS/) | 1GC | Plotting visibilities | [Smirnov et al., 2022](https://ui.adsabs.harvard.edu/abs/2022ASPC..532..385S/abstract) |
| [`Singularity`](https://github.com/hpcng/singularity) | 1GC, FLAG, 2GC, 3GC | Containerisation | [Kurtzer, Sochat & Bauer, 2017](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0177459) |
| [`tricolour`](https://github.com/ska-sa/tricolour) | FLAG | Flagging | [Hugo et al., 2022](https://ui.adsabs.harvard.edu/abs/2022arXiv220609179H/abstract) |
| [`wsclean`](https://gitlab.com/aroffringa/wsclean) | FLAG, 2GC, 3GC | Imaging, model prediction | [Offringa et al., 2014](https://ui.adsabs.harvard.edu/abs/2014MNRAS.444..606O/abstract)|

---

Thank you for visiting.


