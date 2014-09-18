#!/bin/bash
#
# Copyright (C) 2011, 2012 Pablo Barenbaum <foones@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

BASE=PyGobstones-`./gbs.py --version`
DIST=misc/dist_files.txt

if [ ! -e $DIST ]; then
  echo Should be run from PyGobstones root directory.
  exit 1
fi

## copy relevant files

mkdir $BASE
for D in `grep DIR $DIST | cut -d' ' -f2`; do
  mkdir $BASE/$D
  cp $D/*.py $BASE/$D/
done

for F in `grep FILE $DIST | cut -d' ' -f2`; do
  cp $F $BASE/`dirname $F`
done

# make zip
zip -r $BASE.zip $BASE
if [ -d $BASE ]; then
  rm -rf $BASE/
fi

