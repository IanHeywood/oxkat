# setups

This is where 'setup' scripts live. These are `Python` scripts that generate bash files containing sequential calls to various radio astronomy packages, or other `Python` scripts that form part of `oxkat`. Executing the resulting script will run these calls in order or, if you are using a cluster, submit an interdependent batch of jobs to the queue.

The computing infrastructure must be specified when a setup script is run, for example:

```
$ python setups/1GC.py idia
...
$ ./submit_1GC_jobs.sh
```

where `idia` can be replaced with `hippo`, `chpc`, or `node`, the latter being when you want to execute the jobs on your own machine or a standalone node. If you prefer to run software that has been installed directly, 	or inside a `Python` virtual environment, then `Singularity` can be disabled entirely via the `USE_SINGULARITY` switch in the [`config.py`](oxkat/config.py) file.

Rather than having a single `go-pipeline` script, processing jobs are partitioned in stages (1GC, FLAG, 2GC, 3GC), after each of which it is prudent to pause and examine the state of the processing before continuing. If you are gung-ho and don't pay the electricity bill then you can just execute them in order and collect your map at the end.

`oxkat` assumes that your starting point is a typical MeerKAT observation. To process your MeerKAT data they must be in a Measurement Set (MS), containing your target scans as well as suitably-tagged primary and secondary calibrator scans. Clone the contents of the root `oxkat` repo into an empty folder, then copy (or place a symlink to) your MS in the same folder and you will be ready to go. A `Python` pickle file called `project_info.p` will be created towards the start, which contains some deductions about the input MS. This pickle is relied upon throughout the standard workflow. It is possible to use the later stages of `oxkat` to ingest an MS that has been partially processed elsewhere, however it is fiddly, and usually requires some manual editing of the pickle file. This is also part of the reason why the various stages cannot be run all at once, as setup scripts beyond `1GC.py` rely on the `project_info.p` file to generate their jobs.

There follows a description of the available setup scripts, in the order in which they should be run. Technically only the 1GC and FLAG stages are required to obtain a calibrated image of your target(s), however the resulting image can often be significantly improved by direction-independent and direction-dependent self-calibration using the 2GC and 3GC recipes.

---

## 1GC

This stage mostly involves using `CASA` to execute the provided processing scripts. The `1GC.py` setup will look for a single MS in the working folder, and perform the following steps:

* [Duplicate your source MS](), averaging it down to 1024 channels (the default setting, if necessary).	

* [Examine the contents]() of the MS to identify target and calibrator fields. The preferred primary calibrator is either PKS B1934-608 or PKS B0408-65, but others should work as long as `CASA` knows about them. Targets are paired with the secondary calibrator that is closest to them on the sky.

* [Rephase]() the visibilities of the primary calibrator to correct for erroneous positions that were used for the 2019 open-time data (this has no effect on observations that did not have this issue).

* [Apply basic flagging]() commands to all fields.

* [Run autoflaggers]() on the calibrator fields.

* [Split]() the calibrator fields into a `*.calibrators.ms` with 8 spectral windows.

* [Derive intrinsic spectral models]() for the secondary (or secondaries) based on the primary calibrator, using the above MS.

* [Derive delay (***K***), bandpass (***B***), gain (***G***) calibrations]() from the primary and secondary calibrators and apply them to all calibrators and targets. ***K***, ***B***, and ***G*** corrections are derived in an iterative way, with rounds of residual flagging in between.

* [Plot the gain tables]() using `ragavi-gains`.

* [Plot visibilities]() of the corrected calibrator data using `shadeMS`.

* [Split the target data]() out into individual Measurement Sets, with the reference-calibrated data in the `DATA` column of the MS. Note that only basic flagging commands will have been applied to the target data at this stage.

Flagging operations are saved to the `.flagversions` tables at every stage. Products for examination are stored in the `GAINTABLES` and `VISPLOTS` folders.

There is a variant 1GC recipe in `waterhole/setup_1GC_primary_models.py`, which will perform the above steps, but additionally use a clean component model to represent the apparent sky around the primary calibrator (L-band data, PKS B1934-638 only, at present), in addition to the standard model for the calibrator itself. The PKS B1934-638 model is derived from [Benjamin Hugo](https://github.com/bennahugo)'s high dynamic range image of the field, and has eleven spectral points across the band.

Note that only one of the 1GC setup scripts should be run for a given MS. For UHF processing a subset of the band is used to determine the (***K***) and (***G***) solutions, and so the separate `*.calibrators.ms` is not produced.

---

## FLAG

The `FLAG.py` script will pick up where `1GC.py` left off, and perform the following steps for every target in the source MS:

* [Autoflag the target data]() using `tricolour`.

* [Image the targets](), unconstrained deconvolution using `wsclean`.

* [Generate a FITS mask]() of the field using local RMS thresholding.

* [Backup the flag table]().

If you are running on a cluster then the steps above will be submitted for each field in parallel. The resulting image(s) will be available for examination in the `IMAGES` folder.

A variant of this script that performs only the flagging step and not the initial imaging is available in the `waterhole` folder. This is for cases where a cleaning mask for the field is already in hand. Placing the mask in the `IMAGES` folder with a `*<field-name>*.mask0.fits` filename should allow the 2GC script to pick it up automatically and save the extra imaging cycle.


---

## 2GC

The `2GC.py` script performs direction-independent self-calibration. The following steps will be performed for every target MS extracted from the source MS:

* [Masked deconvolution]() of the `DATA` column using `wsclean` and the FITS mask generated by `FLAG.py`.

* [Predict model visibilities]() based on the resulting clean component model using `wsclean`. Note that this is a separate step as baseline dependent averaging is applied during imaging by default to speed up the process.

* [Self calibrate]() the data. The default script now uses CubiCal for this process.

* [Masked deconvolution]() of the `CORRECTED_DATA` using `wsclean`.

* [Refine the FITS mask]() based on the self-calibrated image, and crop it in case it is required later by `DDFacet`.

* [Predict model visibilities]() based on the refined model from the `CORRECTED_DATA` image.

If you are running on a cluster then the steps above will be submitted for each field in parallel. The resulting image(s) will be available for examination in the `IMAGES` folder.

The default `oxkat` settings have automatically produced decent full-band continuum images for a range of of observing scenarios. However the default imaging setup will tend to struggle with fields that contain strong, extended emission, e.g. observations in the Galactic Plane. For fields such as this it might be beneficial to discard the mask produced at the end of the FLAG stage and replace it with a [thresholded mask](https://github.com/IanHeywood/oxkat/blob/master/tools/make_threshold_mask.py) prior to running the 2GC stage. Enabling multiscale in the `wsclean` section of [`config.py`](oxkat/config.py) may also help, and iterative deconvolution with the mask refined at each iteration might be necessary. 

A variant of the 2GC script is `waterhole/setup_2GC_with_multiscale.py`, which uses a lower Briggs' robust value and enables multiscale. This will generally produce better results on fields with large regions of extended emission, although ensuring that a good clean mask is available for this process is critical. 
The older CASA-based self-cal script is now at `waterhole/setup_2GC_CASA.py`.

---

## 3GC

3GC scripts perform direction-dependent self-calibration. `oxkat` has two standard recipes in the form of the `3GC_peel.py` and `3GC_facet.py` script. The first script uses `wsclean` to model and `CubiCal` to peel a single, strong problem source from the visibilities and leave a residual set of visibilities to be subsequently imaged. The second script uses `killMS` to derive directional gain corrections that are then applied by `DDFacet` during imaging. This  is far more likely to be required than the peeling stage, however if both are required then peeling must be done first.

At present, user input is required for both of the 3GC recipes, in the form of DS9 region files (circles only, at present). For peeling, the region file must define the outline of a single problem source, and be passed to the setup script via the `CAL_3GC_PEEL_REGION` parameter in [`config.py`](oxkat/config.py). Note that the default region file points to PKS 0326-288, which is the principal troublemaker in the CDFS field.

For `3GC_facet.py` a region file that defines the centres of the tessels that receive a directional gain correction must be provided in the same folder of the MS. The setup script will automatically look for a file containing the field name with a `.reg` suffix in the working folder. Defaulting to an automatic method in the event that a region file is not found is pending. Note that I've had no success running `DDFacet` or `killMS` on any of the supported cluster environments. Your mileage with these scripts may vary everywhere, but especially here.

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

* [Image the `CORRECTED_DATA` column]() using `DDFacet`

* [Solve for tessel-based gains]() using `killMS`, as defined by the user-provided region file.

* [Re-image the `CORRECTED_DATA` column]() using `DDFacet` with the directional gains applied.

---
