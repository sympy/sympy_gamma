#!/bin/sh

# for debugging info, run:
# ./build.sh -d --line-tracking --source-tracking

# path to the pyjsbuild:
PYJS=~/repos/pyjamas/bin/pyjsbuild


options="$*"
#if [ -z $options ] ; then options="-O";fi
$PYJS --print-statements $options -Itemplates -omedia/js nb
