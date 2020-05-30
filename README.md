# oxkat

![](https://imgur.com/MNCIj5m.jpg)

<b>"Ceci n'est pas une pipe[line]"</b><br> 
(_The Treachery of Images_, René Magritte, 1929)

---

## What is this?

* A set of Python scripts with the aim of (semi-)automatically processing [MeerKAT](https://www.sarao.ac.za/science-engineering/meerkat/) data. 


* At the core is a set of functions that generate calls to various pieces of radio astronomy software, a semi-modular bunch of CASA scripts for performing reference calibration, and a fairly sizeable list of default parameters (at present suitable for full-band Stokes I continuum imaging).


* Job script generation and dependency chains are automatically handled when running on either the [IDIA](https://www.idia.ac.za/) (slurm) cluster or the [CHPC](https://www.chpc.ac.za/)'s [Lengau](https://www.chpc.ac.za/index.php/resources/lengau-cluster) (PBS) cluster.


* Setup scripts glue the above components together into a processing recipe. The default procedure is broken down into stages, after each of which it is advisable to pause and examine the state of the process before continuing.  


* The intention is that the bar to entry is low. If you have stock Python then (at least up to and including the 2GC stage) nothing else needs directly installing apart from [Singularity](https://singularity.lbl.gov/), which is available on both of the clusters mentioned above. All the underlying radio astronomy packages are containerised. 



---

## Usage

1. If you have your [containers all set up](README.md#getting-containers) then log into your machine or cluster, e.g.:

   ```
   ssh ianh@slurm.ilifu.ac.za
   ```

2. Clone this repo somewhere:

   ```
   $ cd ~/Software
   $ git clone https://github.com/IanHeywood/oxkat.git
   ```

3. Navigate to a working area / scratch space:

   ```
   $ cd /scratch/users/ianh/XMM12
   ```

4. Copy these scripts into it (or `git clone` or make a symlink):

   ```
   $ cp -r ~/Software/oxkat/* .
   ```

5. Make a symlink to your MeerKAT Measurement Set (or place it in the working folder, it will not be modified at all):

   ```
   $ ln -s /idia/projects/mightee/1538856059/1538856059_sdp_l0.full_1284.full_pol.ms .
   ```

6. Generate and submit (or run) the jobs required for the reference calibration (1GC):

   ```
   $ python setups/1GC.py <idia|chpc|node >
   $ ./submit_1GC_jobs.sh
   ```

7. If something goes wrong you can kill the 1GC jobs with:

   ```
   $ source SCRIPTS/kill_1GC_jobs.sh
   ```

8. Once this has completed then examine the products, and move to the next steps in the same fashion. 

Please see the [setups README](setups/README.md) for more details. The [config](oxkat/config.py) 

---

## Getting containers

Singularity can be used to download and build containers from [Docker Hub](https://hub.docker.com/). There's a [script](https://github.com/IanHeywood/oxkat/blob/master/tools/pull_containers.sh) included to download them for you. [@SpheMakh](https://github.com/sphemakh)'s [stimela](https://hub.docker.com/u/stimela) project maintains containers for most radio astronomy applications, and repository of pre-built containers is now available at both IDIA and CHPC (in support of the [CARACal](https://github.com/caracal-pipeline) software).

The default container paths are specified in the [config.py](oxkat/config.py) file. The scripts will select the required containers via pattern matching so if a container is replaced with a newer version it should be seamless.

The IDIA slurm head node does not have singularity available, so if you are pulling your own containers that must be done either via a standalone node or a worker node, or otherwise copied over via the `transfer.ilifu.ac.za` node. You will not be able to use the `pull_containers.sh` script on the Lengau head node, and the worker nodes at CHPC do not have external connectivity, so you will have to build the containers elsewhere and then transfer them to CHPC via their `scp.chpc.ac.za` node.

## Beam models

Models for the MeerKAT primary beam at L-band can be downloaded from [here](https://entangled.physics.ox.ac.uk/index.php/s/MkchfHfbI4GUhOg). These are FITS files containing direction and frequency dependent Jones matrices in full polarisation, generated using the [Eidos](https://github.com/ratt-ru/eidos) package ([Asad et al., 2018](https://ui.adsabs.harvard.edu/abs/2019arXiv190407155A/abstract)).

## Software package roll-call

| Package| Purpose | Reference |
| --- | --- | --- | 
| [`CASA`](https://casa.nrao.edu/) | Averaging, splitting, cross calibration, DI self-calibration, flagging | [McMullin et al., 2007](https://ui.adsabs.harvard.edu/abs/2007ASPC..376..127M/abstract)|
| [`CubiCal`](https://github.com/ratt-ru/CubiCal) | DI / DD self-calibration | [Kenyon et al., 2018](https://ui.adsabs.harvard.edu/abs/2018MNRAS.478.2399K/abstract)|
| [`DDFacet`](https://github.com/saopicc/DDFacet) | Imaging with direction-dependent corrections, model prediction | [Tasse et al., 2018](https://ui.adsabs.harvard.edu/abs/2018A%26A...611A..87T/abstract) | 
| [`killMS`](https://github.com/saopicc/killMS) | DD self-calibration| - |
| [`PyBDSF`](https://www.astron.nl/citt/pybdsf/) | Source cataloguing (during DD self-calibration) | [Mohan & Rafferty, 2017](https://ui.adsabs.harvard.edu/abs/2015ascl.soft02007M/abstract) |
| [`ragavi`](https://github.com/ratt-ru/ragavi/) |  Plotting gain solutions| - |
| [`shadeMS`](https://github.com/ratt-ru/shadeMS/) | Plotting visibilities| - |
| [`tricolour`](https://github.com/ska-sa/tricolour) | Flagging | - |
| [`wsclean`](https://sourceforge.net/p/wsclean/wiki/Home/) | Imaging, model prediction | [Offringa et al., 2014](https://ui.adsabs.harvard.edu/abs/2014MNRAS.444..606O/abstract)|

---

## Notes

* This was originally just a place to store my MeerKAT processing recipes. Several people have since found these scripts useful, and I hope that you do too. I have spent time on text such as this and tried to improve user-friendliness in that hope. But please note that everything here is subject to change.


* The standard setup scripts should do a decent job on fields that are dominated by compact sources (e.g. extragalactic deep fields). Pointings that contain morphologically complex emission (e.g. the Galactic Plane) benefit from iterative deconvolution runs with manual or thresholded masking.


* A revised setup script for 3GC calibration is pending.


* Please file bugs / suggestions etc. as [issues](https://github.com/IanHeywood/oxkat/issues).


Thanks for visiting.


