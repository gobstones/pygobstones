#!/usr/bin/python
# coding:utf-8
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

#BASE = '../'
BASE = './'

import sys
sys.path.append(BASE)

import time
import os

#if not os.path.exists(os.path.basename(sys.argv[0])):
#    sys.stderr.write('\nError: debian_dist -- should be run from its own directory (cd misc/)\n\n')
#    sys.exit(1)

SHARED = '/usr/share/pyshared/pygobstones'

def changelog(): 
    f = open(BASE + 'changelog', 'w')
    f.write('pygobstones (%s) unstable; urgency=low\n' % (VER,))

    for line in os.popen('hg log').readlines():
        if line.startswith('summary: '):
            f.write('    * %s\n' % (line[9:].strip(' \t\r\n'),))
    f.write(' -- Pablo Barenbaum <foones@gmail.com>  %s\n' % (
            time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime()),
        )
    )
    f.close()

import common.utils

VER = common.utils.version_number()

changelog()

f = open(BASE + 'pygobstones-%s' % (VER,), 'w')
f.write('Package: pygobstones\n')
f.write('Section: python\n')
f.write('Homepage: http://pygobstones.wordpress.com\n')
f.write('Priority: optional\n')
f.write('Version: %s\n' % (VER,))
f.write('Architecture: all\n')
f.write('Changelog: changelog\n')
f.write('Maintainer: Pablo Barenbaum <foones@gmail.com>\n')
f.write('Readme: doc/README.txt\n')
f.write('Depends: python (>= 2.6), python-tk\n')
f.write('Description: Intérprete para el lenguaje de programación Gobstones.\n')
for line in open(BASE + 'doc/README.txt', 'r'):
    if line.strip(' \t\r\n') == '':
        f.write(' .\n')
    else:
        f.write(' ' + line)
f.write('Extra-Files: doc/README.txt, common/LICENSE.txt\n')
f.write('Files:')
for line in open('misc/dist_files.txt', 'r'):
    typ, res = line.strip(' \t\r\n').split(' ')
    assert typ in ['DIR', 'FILE']
    files = []
    if typ == 'DIR':
        for x in os.listdir(BASE + res):
            if not x.endswith('.py'): continue
            files.append('%s/%s' % (res, x))
    elif typ == 'FILE':
        files.append(res)

    for x in files:
        y = x
        if y.endswith('.pyw'):
            y = y[:-4] + '.py'
        f.write(' %s %s/%s\n' % (x, SHARED, y))

for binsrc, bindst in [('Main', 'pygobstones'),
                       ('gbs', 'gbs')]:
    g = open(BASE + '_bin_%s_.py' % (bindst,), 'w')
    g.write('#!/usr/bin/python\n')
    g.write('import sys\n')
    g.write('sys.path.append("%s")\n' % (SHARED,))
    g.write('import %s\n' % (binsrc,))
    g.write('%s.main()\n' % (binsrc,))
    g.close()
    f.write(' _bin_%s_.py /usr/bin/%s\n' % (bindst, bindst))

f.close()

os.system('cd %s && equivs-build pygobstones-%s' % (BASE, VER,))
os.system('rm %s_bin_pygobstones_.py' % (BASE,))
os.system('rm %s_bin_gbs_.py' % (BASE,))
os.system('rm %schangelog' % (BASE,))
os.system('rm %spygobstones-%s' % (BASE, VER,))

