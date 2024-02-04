# containers

The radio astronomy packages that make `oxkat` work are provided in `Singularity` containers based on Ubuntu 20.04. Due to dependency conflicts between the underlying packages there are four of these. Three of these volumes loosely correspond to the 1GC, 2GC and 3GC stages, and there is a standalone container for `tricolour`, which at the moment doesn't seem to play nicely with anyone else. The principal contents of each container are provided below.

#### oxkat-0.5_vol1.sif

```
casa 6.6.0
ragavi 0.5.2
```

#### oxkat-0.5_vol2.sif

```
astropy 5.2.2
breizorro 0.1.2
cubical 1.6.4
montage 6.0
owlcat 1.7.9
pypher 0.7.1
quartical 0.2.2
shadems 0.5.3
smops 0.1.7
wsclean 3.4
```

#### oxkat-0.5_vol3.sif

```
astropy 5.1
ddfacet 0.7.2
killms 3.1.0
pybdsf 1.10.3
```

#### oxkat-0.5_tricolour.sif

```
tricolour 0.1.8
```
