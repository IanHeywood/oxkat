#!/usr/bin/env bash

singularity pull docker://stimela/tricolour:1.1.3
singularity pull docker://stimela/wsclean:1.1.5
singularity pull docker://stimela/cubical:1.1.5
singularity pull docker://stimela/codex-africanus:dev
singularity pull docker://bhugo/ddfacet:0.4.1
singularity pull docker://bhugo/killms:2.7.0