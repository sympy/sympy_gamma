#!/bin/sh

# for debugging info, run:
# ./build.sh -d --line-tracking --source-tracking

options="$*"
#if [ -z $options ] ; then options="-O";fi
~/repos/pyjamas/bin/pyjsbuild --print-statements $options index
