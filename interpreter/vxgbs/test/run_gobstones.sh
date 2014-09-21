#!/bin/bash
INTERP=python    # for the standard Python implementation
#INTERP=python2.3  # 2.3 version
#INTERP=pypy      # PyPy

GBS_OPTS="--no-liveness --no-print-board"

## Interpret directly
$INTERP ../gbs.py $GBS_OPTS $1 --from $2 --silent #2>/dev/null

## Dump bytecode and interpret
#$INTERP ../gbs.py $GBS_OPTS examples/test.gbs --asm examples/test.gbo --style compact --silent
#$INTERP ../gbs.py $GBS_OPTS examples/test.gbo --from empty.gbb --to examples/out_py.gbb --silent #2>/dev/null

## JIT compiler 
#$INTERP ../gbs.py --jit $GBS_OPTS examples/test.gbs --from empty.gbb --to examples/out_py.gbt --silent #2>/dev/null

## Dump bytecode + JIT compiler
#$INTERP ../gbs.py $GBS_OPTS examples/test.gbs --asm examples/test.gbo --style compact --silent
#$INTERP ../gbs.py $GBS_OPTS examples/test.gbo --from empty.gbb --jit --to examples/out_py.gbb --silent #2>/dev/null
