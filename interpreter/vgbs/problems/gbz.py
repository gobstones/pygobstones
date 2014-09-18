#!/usr/bin/python
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

import sys
sys.path.append('../')

import os
import zipfile
import tempfile

import common.utils
import lang.judge.gbs_judge as gbs_judge

def report_error(errtype, msg):
  sys.stderr.write('%s:\n' % (errtype,))
  sys.stderr.write('%s\n' % (common.utils.indent(msg),))

def report_program_error(errtype, msg, area):
  sys.stderr.write('\n%s\n' % (area,))
  report_error(errtype, msg)

def report_source_exception(exception):
  report_program_error(exception.error_type(), exception.msg, exception.area)

def errline(s):
  sys.stderr.write('%s\n' % (s,))

if len(sys.argv) != 2:
  sys.stderr.write('Usage: %s problem_set.txt\n' % (sys.argv[0],))
  sys.exit(1)

problem_set = sys.argv[1]

if not os.path.exists(problem_set):
  sys.stderr.write('File "%s" does not exist\n' % (problem_set,))
  sys.exit(1)

base = os.path.basename(problem_set) 
if len(base) >= 4 and base[-4:] == '.txt':
  base = base[:-4]
zipfn = base + '.gbz'

zf = zipfile.ZipFile(zipfn, 'w', zipfile.ZIP_DEFLATED)
bundle = gbs_judge.SourceProblemBundle(problem_set)
zf.write(problem_set, '__GBZ__')

for bfn in bundle.common_boards():
  zf.write(bfn, '_boards/' + os.path.basename(bfn))

for problem in bundle.problems():
  sys.stderr.write('** Processing problem %s\n' % (problem,))

  # copy files
  for fn in bundle.files_for_problem(problem):
    zf.write(fn, problem + "/" + os.path.basename(fn))

  code_dict = gbs_judge.CodeDictionaryFromSolution(
				bundle, problem,
				bundle.solution_for(problem),
				bundle.solution_path_for(problem),
				log=errline)

  if code_dict.status == 'FAILED':
    sys.stderr.write('! Error: Could not create problem "%s".\n' % (problem,))
    sys.stderr.write('! It fails on the following test cases:\n')
    report_source_exception(code_dict.exception)
    sys.exit(1)

  # fingerprints
  td = gbs_judge.TestDriver(bundle, problem, code_dict,
                            fn=os.path.normpath(bundle.solution_path_for(problem)),
                            log=errline)
  r = td.run()
  #if r == 'FAILED':
  #  sys.stderr.write('! Error: Could not create problem "%s".\n' % (problem,))
  #  sys.stderr.write('! It fails on the following test cases:\n')
  #  report_source_exception(td._error_exception)
  #  sys.exit(1)

  def save_compiled_code():
    for source_name in bundle.test_source_names(problem):
      tmp_fd, tmp_path = tempfile.mkstemp()
      tmpf = open(tmp_path, 'w')
      bundle.dump_compiled_code(problem, source_name, tmpf)
      tmpf.close()
      obj_name = gbs_judge.object_for(source_name)
      zf.write(tmp_path, problem + "/" + obj_name)
      os.close(tmp_fd)
      os.remove(tmp_path)

  save_compiled_code()

zf.close()
sys.stderr.write('Wrote %s\n' % (zipfn,))

