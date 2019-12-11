#!/usr/bin/env bash

singularity pull docker://stimela/tricolour:dev
singularity pull docker://stimela/wsclean:1.2.3
singularity pull docker://stimela/cubical:1.2.3
singularity pull docker://stimela/codex-africanus:dev
singularity pull docker://bhugo/ddfacet:0.5.0
singularity pull docker://bhugo/killms:2.7.0