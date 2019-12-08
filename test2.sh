#!/bin/bash

set -euo pipefail
file=${1:-}

first-info ()
{
    cat $file | sed '/^$/d' | sed '/###/d' | sed 's/^\s*\(.*\)\s*/\1/g'
}

first-info


