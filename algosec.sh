#!/bin/bash

# check for any pyhton version
for PYTHON in python2.6 python2.7 python3.0 python3.1 python3.2 python3.3 python3.4 python3.5 python3.6 python3.7 python3.8 python3.9 python3.10 python3.11 python3.12 python
#for PYTHON in python3.0 python3.1 python3.2 python3.3 python3.4 python3.5 python3.6 python3.7 python3.8 python3.9 python3.10 python3.11 python3.12 python
do
    $PYTHON -V 1> /dev/null 2>&1 && break
done

if [ -z "$PYTHON" ]
then
    echo Python is required but it could not be found 1>&2
    echo Check if it is installed and is in the PATH variable 1>&2
fi

PYVER=$($PYTHON -V 2>&1 | sed -En 's/.*Python\s([0-9]+)\..*/\1/p')

[ $PYVER -lt 3 ] && {
    #PYVER=$($PYTHON -V 2>&1 | sed -En 's/.*Python\s([0-9]+\.[0-9]+\.[0-9]+).*/\1/p')
    PYVER=$($PYTHON -V 2>&1 | sed -En 's/.*Python\s(([0-9]+\.)+[0-9]+).*/\1/p')
    echo "Python 3 or later is required but version $PYVER was found" 1>&2
    exit 1
}

INFILE=$1
[ -z "$INFILE" ] && INFILE=ip_list.txt

[ -f "$INFILE" ] || {
    echo File \'$INFILE\' not found 1>&2
    exit 1
}

LCKFILE=$0.lock

[ -f "$LCKFILE" ] && {
    echo There is an instance of $0 already running 1>&2
    exit 1
}

echo $(date +'YYYY-mm-dd') > ${LCKFILE}

SRCPATH=$(dirname "$0")

shift

echo $PYTHON -W ignore "${SRCPATH}/bin/extractor.py" $* "$INFILE"

[ -f "$LCKFILE" ] && rm "$LCKFILE"

INFILE=""
PYTHON=""
SRCPATH=""
LCKFILE=""