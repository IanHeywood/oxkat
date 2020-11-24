# setups

This is where 'setup' scripts live. These generate bash files containing sequential calls to various radio astronomy packages, or other Python tools that form part of `oxkat`. Executing the resulting script will run these calls in order or, if you are using a cluster, submit an interdependent batch of jobs to the queue.

The computing infrastructure must be specified when a setup script is run, for example:

```
$ python setups/1GC.py idia
```

where `idia` can be replaced with `hippo`, `chpc`, or `node`, the latter being when you want to execute the jobs on your own machine or a standalone node. If you prefer to run things natively or inside a Python virtual environment, then singularity can be disabled entirely via the `USE_SINGULARITY` switch in the [`config.py`](oxkat/config.py) file.

Rather than having a single `go-pipeline` script, processing jobs are partitioned in stages ([1GC](README.md#1gcpy), [FLAG](README.md#flagpy), [2GC](README.md#2gcpy), [3GC](README.md#3gcpy)), after each of which it is prudent to pause and examine the state of the processing before continuing. If you are gung-ho and don't pay the electricity bill then you can just execute them in order and collect your map at the end.

`oxkat` assumes that your starting point is a typical MeerKAT observation. To process your MeerKAT data they must be in a Measurement Set (MS), containing your target scans as well as suitable primary and secondary calibrator scans. Clone the contents of the root `oxkat` repo into an empty folder, then copy (or place a symlink to) your Measurement Set in the same folder and you will be ready to go. There follows a description of the available setup scripts, in the order in which they should be run. Technically only the 1GC and FLAG stages are required to obtain a calibrated image of your flagged target(s), however the resulting image can often be significantly improved by direction-independent and direction-dependent self-calibration using the 2GC and 3GC recipes.

---

## 1GC.py

This stage mostly involves using `CASA` to execute the provided processing scripts. 

* [Duplicate your source MS](), averaging it down to 1,024 channels (if necessary).	

* [Examine the contents]() of the MS to identify target and calibrator fields. The preferred primary calibrator is either PKS B1934-608 or PKS B0408-65, but others should work as long as `CASA` knows about them. Targets are paired with the secondary calibrator that is closest to them on the sky.

* [Rephase]() the visibilities of the primary calibrator to correct for erroneous positions that were present in the open time data (this has no effect on observations that did not have this issue).

* [Apply basic flagging]() commands to all fields.

* [Run autoflaggers]() on the calibrator fields.

* [Split]() the calibrator fields into a `*.calibrators.ms` with 8 spectral windows.

* [Derive intrinsic spectral models]() for the secondary (or secondaries) based on the primary calibrator, using the above MS.

* [Derive delay (***K***), bandpass (***B***), gain (***G***) calibrations]() from the primary and secondary calibrators and apply them to all calibrators and targets. ***K***, ***B***, and ***G*** corrections are derived in an iterative way, with rounds of residual flagging in between.

* [Plot the gain tables]() using `ragavi-gains`.

* [Plot visibilities]() of the corrected calibrator data using `shadeMS`.

* [Split the target data]() out into individual Measurement Sets, with the reference calibrated data in the `DATA` column of the MS. Note that only basic flagging commands will have been applied to the target data at this stage.

Flagging operations are saved to the `.flagversions` tables at every stage. Products for examination are stored in the `GAINTABLES` and `VISPLOTS` folders.

There is a variant 1GC recipe in `1GC_primary_models.py`, which will perform the above steps, but additionally use a clean component model to represent the full sky around the primary calibrator (PKS B1934-638 only, at present), in addition to the standard model for the calibrator itself. The PKS B1934-638 model is derived from [Benjamin Hugo](https://github.com/bennahugo)'s high dynamic range image of the field, and has eleven spectral points across the band.

Note that only one of the 1GC setup scripts should be run for a given MS.

---

## FLAG.py

This script will perform the following steps for every target in the source MS:

* [Autoflag the target data]() using `tricolour`.

* [Image the targets](), unconstrained deconvolution using `wsclean`.

* [Generate a FITS mask]() of the field using local RMS thresholding.

* [Backup the flag table]().

* [Copy DATA to CORRECTED_DATA]() (see below).

If you are running on a cluster then the steps above will be submitted for each field in parallel. The resulting image(s) will be available for examination in the `IMAGES` folder.

---

## 2GC.py

This script will perform the following steps for every target in the source MS:

* [Masked deconvolution]() using `wsclean` and the FITS mask generated by `FLAG.py`.

* [Predict model visibilities]() based on the resulting clean component model using `wsclean`. Note that this is a separate step as baseline dependent averaging is applied during imaging by default to speed up the process.

* [Self calibrate]() the data.

* [Masked deconvolution]() of the `CORRECTED_DATA` using `wsclean`.

* [Refine the FITS mask]() based on the self-calibrated image, and crop it in case it is required later by `DDFacet`.

* [Predict model visibilities]() based on the refined model from the `CORRECTED_DATA` image.

If you are running on IDIA or CHPC hardware then the steps above will be submitted for each field in parallel. The resulting image(s) will be available for examination in the `IMAGES` folder.

The default `oxkat` settings have automatically produced decent full-band continuum images for a range of of observing scenarios. However the default imaging setup will tend to struggle with fields that contain strong, extended emission, e.g. observations in the Galactic Plane. For fields such as this it is recommended to discard the mask produced at the end of the FLAG stage and replace it with a [thresholded mask](https://github.com/IanHeywood/oxkat/blob/master/tools/make_threshold_mask.py) prior to running the 2GC stage. Enabling multiscale in the `wsclean` section of [`config.py`](oxkat/config.py) may also be beneficial. The mask can be refined and the process repeated by re-running the 2GC recipe. This is generally not required, but making the 2GC stage iterable is the motivation for copying `DATA` to `CORRECTED_DATA` at the end of the FLAG stage.

---

## 3GC_peel.py

**Big caveat:** The software required for this stage cannot generally be run via the IDIA slurm queue. It will not run at all on CHPC's Lengau cluster due to the configuration of the worker nodes. Using `salloc` to acquire a HighMem worker node at IDIA and then running the resulting jobs in `node` mode is probably the best approach if you do not have access to a suitable machine of your own. Note that DD-calibration and imaging is very resource heavy. Note also that there generally isn't a single approach for DD cal (or even DI cal) that works for every field.

[**PENDING**]
