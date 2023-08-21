# setups

This is where 'setup' scripts live. These are `Python` scripts that generate bash files containing sequential calls to various radio astronomy packages, or other `Python` scripts that form part of `oxkat`. Executing the resulting script will run these calls in order or, if you are using a cluster, submit an interdependent batch of jobs to the queue.

The computing infrastructure must be specified when a setup script is run, for example:

```
$ python setups/1GC.py idia
...
$ ./submit_1GC_jobs.sh
```

where `idia` can be replaced with `hippo`, `chpc`, or `node`, the latter being when you want to execute the jobs on your own machine or a standalone node. If you prefer to run software that has been installed directly, 	or inside a `Python` virtual environment, then `Singularity` can be disabled entirely via the `USE_SINGULARITY` switch in the [`config.py`](oxkat/config.py) file.

Processing jobs are partitioned in stages, the full ordering being GET_INFO, 1GC, FLAG, 2GC, 3GC_peel, 3GC_facet. After each stage it is prudent to pause and examine the state of the processing before continuing. If you are gung-ho and don't pay the electricity bill then you can just execute them in order and collect your map at the end, although the 3GC peeling and facet-based calibration require the user to provide some region files to guide the direction-dependent calibration.

`oxkat` assumes that your starting point is a typical MeerKAT observation. To process your MeerKAT data they must be in a Measurement Set (MS), containing your target scans as well as suitably-tagged primary and secondary calibrator scans. Clone the contents of the root `oxkat` repo into an empty folder, then copy (or place a symlink to) your MS in the same folder and you will be ready to go. A `JSON` file called `project_info.json` will be created by the initial GET_INFO script, which contains some deductions about the input MS. This JSON file is relied upon throughout the standard workflow. It is possible to use the later stages of `oxkat` to ingest an MS that has been partially processed elsewhere, however it is fiddly, and might require some manual editing of the project info file or setup scripts.

There follows a description of the available setup scripts, in the order in which they should be run. Technically only the 1GC and FLAG stages are required to obtain a calibrated image of your target(s), however the resulting image can often be significantly improved by direction-independent and direction-dependent self-calibration using the 2GC and 3GC recipes, as well as the more robust deconvolution that these stages provide.

---

## GET_INFO

This initial step will:

* [Determine the observing band]() (UHF, L-band, or one of the five S-band sub-bands).

* [Examine the contents]() of the MS to identify target and calibrator fields. The preferred primary calibrator is either PKS B1934-608 or PKS B0408-65, but others should work as long as `CASA` knows about them. 

* [Pair targets with the secondary calibrator]() that is closest to them on the sky.

* [Select a preferred reference antenna]() based on minimal flag percentages.

* Produce an `msinfo` log file containing information about the observation (similar to `CASA`'s `listobs` task).

* Produce a `sun` log file that lists the absolute and relative positions of the Sun and Moon on a per-scan basis.

* Produce a `scantimes` log file that has detailed information about the timestamps of each scan, useful for variability studies.

* Write the relevant information to a `JSON` file that is read and relied upon by subsequent steps.

---

## 1GC

This stage mostly involves using `CASA` to execute the provided processing scripts. The `1GC.py` setup will look for a single MS in the working folder, and perform the following steps:

* [Duplicate your source MS](), averaging it down to 1024 channels (the default setting, if necessary).	

* [Rephase]() the visibilities of the primary calibrator to correct for erroneous positions that were used for the 2019 open-time data (this has no effect on observations that did not have this issue).

* [Apply basic flagging]() commands to all fields.

* [Run autoflaggers]() on the calibrator fields.

* [Derive delay (***K***), bandpass (***B***), gain (***G***) calibrations]() from the primary and secondary calibrators and apply them to all calibrators and targets. ***K***, ***B***, and ***G*** corrections are derived in an iterative way, with rounds of residual flagging in between.

* [Plot the gain tables]() using `ragavi-gains`.

* [Plot visibilities]() of the corrected calibrator data using `shadeMS`.

* [Split the target data]() out into individual Measurement Sets, with the reference-calibrated data in the `DATA` column of the MS. Note that only basic flagging commands will have been applied to the target data at this stage.

Flagging operations are (optionally) saved to the `.flagversions` tables at every stage. Products for examination are stored in the `GAINTABLES` and `VISPLOTS` folders.

There is a variant 1GC recipe in `waterhole/setup_1GC_primary_models.py`, which will perform the above steps, but additionally use a clean component model to represent the apparent sky around the primary calibrator (L-band data, PKS B1934-638 only, at present), in addition to the standard model for the calibrator itself. The PKS B1934-638 model is derived from [Benjamin Hugo](https://github.com/bennahugo)'s high dynamic range image of the field, and has eleven spectral points across the band.

---

## FLAG

The `FLAG.py` script will pick up where `1GC.py` left off, and perform the following steps for every target in the source MS:

* [Autoflag the target data]() using `tricolour`.

* [Image the targets](), unconstrained deconvolution using `wsclean`.

* [Generate a FITS mask]() of the field using local RMS thresholding.

* (Optionally) [backup the flag table]().

If you are running on a cluster then the steps above will be submitted for each field in parallel. The resulting image(s) will be available for examination in the `IMAGES` folder.

A variant of this script that performs only the flagging step and not the initial imaging is available in the `waterhole` folder. This is for cases where a cleaning mask for the field is already in hand. Placing the mask in the `IMAGES` folder with a `*<field-name>*.mask0.fits` filename should allow the 2GC script to pick it up automatically and save the extra imaging cycle.


---

## 2GC

The `2GC.py` script performs direction-independent self-calibration. The following steps will be performed for every target MS extracted from the source MS:

* [Masked deconvolution]() of the `DATA` column using `wsclean` and the FITS mask generated by `FLAG.py`.

* [Predict model visibilities]() based on the resulting clean component model using `wsclean`.

* [Self calibrate]() the data. The default script now uses CubiCal for this process.

* [Masked deconvolution]() of the `CORRECTED_DATA` using `wsclean`.

* [Predict model visibilities]() based on the refined model from the `CORRECTED_DATA` image.

* [Refine the FITS mask]() based on the self-calibrated image, and crop it in case it is required later by `DDFacet`.

If you are running on a cluster then the steps above will be submitted for each field in parallel. The resulting image(s) will be available for examination in the `IMAGES` folder.

The default `oxkat` settings have automatically produced decent full-band continuum images for a range of of observing scenarios. However the default imaging setup will tend to struggle with fields that contain strong, extended emission, e.g. observations in the Galactic plane. For fields such as this it might be beneficial to discard the mask produced at the end of the FLAG stage and replace it with a [thresholded mask](https://github.com/IanHeywood/oxkat/blob/master/tools/make_threshold_mask.py) prior to running the 2GC stage. Enabling multiscale in the `wsclean` section of [`config.py`](oxkat/config.py) may also help, and iterative deconvolution with the mask refined at each iteration might be necessary. 

A variant of the 2GC script is `waterhole/setup_2GC_with_multiscale.py`, which uses a lower Briggs' robust value and enables multiscale. This will generally produce better results on fields with large regions of extended emission, although ensuring that a good clean mask is available for this process is critical. 
The older CASA-based self-cal script is now at `waterhole/setup_2GC_CASA.py`.

---

## 3GC

3GC scripts perform direction-dependent self-calibration. `oxkat` has two standard recipes in the form of the `3GC_peel.py` and `3GC_facet.py` script. The first script uses `wsclean` to model and `CubiCal` to peel a single, strong problem source from the visibilities and leave a residual set of visibilities to be subsequently imaged. The second script uses `killMS` to derive directional gain corrections that are then applied by `DDFacet` during imaging. This is far more likely to be required than the peeling stage, however if both are required then peeling must be done first.

At present, user input is required for both of the 3GC recipes, in the form of DS9 region files (circles only, at present). For peeling, the region file must define the outline of a single problem source. The peeling region can be passed to the setup script via the `CAL_3GC_PEEL_REGION` parameter in [`config.py`](oxkat/config.py). The source defined by this region will then be peeled from all of the target sources in the MS, an example use-case being a close-packed mosaic that are all blighted by the same problem source. Alternatively a region file of the format `*<fieldname>*peel*.reg` can be placed in the working folder, and this will be picked up automatically. Fields that do not have a corresponding region file will not be peeled.

For `3GC_facet.py` a region file that defines the centres of the tessels that receive a directional gain correction must be provided in the same folder of the MS. The region file rules are the same as for the peeling stage. If the `CAL_3GC_FACET_REGION` parameter in [`config.py`](oxkat/config.py) is not set, then the setup script will automatically look for a region file of the format `*<fieldname>*facet*.reg` suffix in the working folder. The 3GC facet calibration step now seems to work (albeit quite slowly) on the IDIA / ilifu cluster, but requires the HighMem nodes, of which there are only two.

#### 3GC_peel.py

If your original MS has multiple fields then move the target Measurement Sets that you do not wish to process out of the working folder, leaving only the MS with the problem source. If you have defined the region file and set the relevant parameter in [`config.py`](oxkat/config.py), then the `3GC_peel.py` script will setup the following steps:

* [Generate a model]() of the field with higher angular and frequency resolution using `wsclean`.

* [Partition the model]() into a second FITS cube containing only the problem source.

* [Predict model visibilites]() for the problem source, and store these in a custom MS column (default name: `DIR1_DATA`).

* [Predict model visibilites]() for the full sky model and store these in `MODEL_DATA`.

* [Peel the problem source]() using `CubiCal`, storing the corrected visibilites with the `DIR1_DATA` subtracted in `CORRECTED_DATA`.

The `CORRECTED_DATA` column must then be imaged, or the resulting MS can be passed to `3GC_facet.py` for further direction-dependent corrections.

#### 3GC_facet.py

The following steps will be performed for every target in the source MS:

* [Image the `CORRECTED_DATA` column]() using `DDFacet`.

* [Solve for tessel-based gains]() using `killMS`, as defined by the user-provided region file.

* [Re-image the `CORRECTED_DATA` column]() using `DDFacet` with the directional gains applied.

---
