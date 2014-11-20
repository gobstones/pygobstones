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

import os
import re
import sys
import zipfile
import tempfile
import shutil

import common.utils
import common.i18n as i18n

import lang.judge
import lang.board.formats
import lang.gbs_board
import lang.bnf_parser
import lang.gbs_parser
import lang.gbs_lint
import lang.gbs_compiler
import lang.gbs_vm
import lang.gbs_vm_serializer
import lang.gbs_builtins
import lang.gbs_board

def read_problem_tree(f):

    def level(x):
        i = 0
        while x[i] == '>':
            i += 1
        return i

    d = {}
    lst0 = common.utils.read_stripped_lines(f)
    tree = []
    for x in lst0:
        lv = level(x)
        if lv == 0:
            tree[-1].append(x)
        else:
            while len(tree) >= level(x):
                sub = tree.pop()
                tree[-1].append(sub)
            tree.append([x[lv:]])
    while len(tree) > 1:
        sub = tree.pop()
        tree[-1].append(sub)
    return tree[0]

def problem_tree_to_list(tree):
    if isinstance(tree, list):
        res = []
        for x in tree[1:]:
            res.extend(problem_tree_to_list(x))
        return res
    else:
        return [tree]

def read_dict_file(f):
    d = {}
    for l in common.utils.read_stripped_lines(f):
        k, v = l.split(' ')
        assert v in ['True', 'False']
        if v == 'True':
            d[k] = True
        else:
            d[k] = False
    return d

def object_for(s):
    if s.endswith('.gbs'):
        s = s[:-4]
    s += '.gbo'
    return s

class GbsRun(object):

    def __init__(self, run_name, program_name, board_name):
        self._run_name = run_name
        self._program_name = program_name
        self._board_name = board_name

    def id(self):
        return '%s_%s' % (self._program_name, self._board_name.replace('/', '.'))

    def run_name(self):
        return self._run_name

    def program_name(self):
        return self._program_name

    def board_name(self):
        return self._board_name

def read_run_file(problem, prefix, f):
    res = []
    i = 0
    for l in common.utils.read_stripped_lines(f):
        i += 1
        t = l.split(' ')
        assert len(t) == 2
        name = '%s.%s%u' % (problem, prefix, i)
        res.append(GbsRun(name, t[0], t[1]))
    return res

def collect_bundles():
    res = []
    for dr in lang.judge.Bundle_lookup_path:
        try:
            dr_contents = os.listdir(dr)
        except OSError:
            continue
        for bn in dr_contents:
            fn = os.path.join(dr, bn)
            if len(fn) >= 3 and fn[-3:].lower() == 'gbz':
                try:
                    zf = zipfile.ZipFile(fn, 'r')
                except: # zipfile.BadZipfile
                    continue
                if '__GBZ__' in zf.namelist():
                    res.append(fn)
                zf.close()
    return res

class ProblemBundle(object):
    def test_source_names(self, problem):
        res = []
        for tc in self.test_cases_for(problem):
            res.append(tc.program_name())
        return common.utils.seq_no_repeats(res)

class SourceProblemBundle(ProblemBundle):

    def __init__(self, problem_set):
        self._path = os.path.dirname(problem_set)
        f = open(problem_set, 'r')
        self._problem_tree = read_problem_tree(f)
        f.close()
        self._problem_list = problem_tree_to_list(self._problem_tree)

    def files_for_problem(self, problem):
        fs = []
        for x in os.listdir(os.path.join(self._path, problem)):
            if x != 'Solution.gbs':
                fs.append(os.path.join(self._path, problem, x))
        return fs

    def problems(self):
        return self._problem_list

    def options(self, problem): 
        assert problem in self._problem_list
        f = open(os.path.join(self._path, problem, 'problem_type.txt'))
        opts = read_dict_file(f)
        f.close()
        return opts

    def solution_path_for(self, problem): 
        return os.path.join(self._path, problem, 'Solution.gbs')

    def solution_for(self, problem): 
        return common.utils.read_file(self.solution_path_for(problem))

    def test_cases_for(self, problem):
        f = open(os.path.join(self._path, problem, 'tests.txt'))
        res = read_run_file(problem, 'test', f)
        f.close()
        return res

    def load_source(self, problem, source_name):
        f = open(os.path.join(self._path, problem, source_name), 'r')
        src = f.read()
        f.close()
        return src

    def load_board(self, problem, board_name):
        fn = os.path.join(self._path, board_name)
        fmt = lang.board.formats.format_for(fn)
        board = lang.gbs_board.Board((1, 1))
        f = open(fn, 'r')
        board.load(f, fmt)
        f.close()
        return board

    def common_boards(self):
        if not os.path.exists(os.path.join(self._path, '_boards')):
            return []
        res = []
        for bfn in os.listdir(os.path.join(self._path, '_boards')):
            res.append(os.path.join(self._path, '_boards', bfn))
        return res

    def dump_compiled_code(self, problem, source_name, outf):
        contents = self.load_source(problem, source_name)
        fn = os.path.join(self._path, problem, source_name)
        code = compile_source(contents, fn=fn)
        lang.gbs_vm_serializer.dump(code, outf, style='compact')

_statement_template = '''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>
  <head>
      <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
      <meta name="generator" content="PyGobstones$VERSION">
      <title>$TITLE</title>
      <style type="text/css">')
body {
    font-family: Verdana, helvetica;
    font-size: 10pt;
}
.statement {
    width: 50%;
}
p {
    text-indent: 1cm;
}
h1 {
    border: black solid 1px;
    padding: 10px;
}
      </style>
  </head>
  <body>
  <h1>$TITLE</h1>
  <div class="statement">
  $STATEMENT
  </div>
  </body>
</html>
'''

def zip_path_join(*args):
    return '/'.join(args)

def zipfile_stream(zf, filename):
    # The body of this function should be conceptually
    #     return zf.open(filename).
    #
    # We can't use that directly because zf.open is available
    # only in Python >= 2.6.
    #
    # Also, in Python 3.1, we must wrap the output
    # in an io.TextIOWrapper for the lines to be read as.
    # strings (not as bytes).
    #
    if common.utils.python_major_version() < 3:
        return zf.open(filename)
        # For still older Python versions:
        #     return common.utils.StringIO(zf.read(filename))
    else:
        import io
        return io.TextIOWrapper(zf.open(filename))

class GbzProblemBundle(ProblemBundle):

    def __init__(self, zipname):
        self._fn = zipname

        zf = zipfile.ZipFile(self._fn)
        f = zipfile_stream(zf, '__GBZ__')
        self._problem_tree = read_problem_tree(f)
        f.close()
        zf.close()
        self._problem_list = problem_tree_to_list(self._problem_tree)

    def options(self, problem): 
        zf = zipfile.ZipFile(self._fn)
        f = zipfile_stream(zf, zip_path_join(problem, 'problem_type.txt'))
        opts = read_dict_file(f)
        f.close()
        zf.close()
        return opts

    def problems(self):
        return self._problem_list

    def problem_tree(self):
        return self._problem_tree

    def problem_statement(self, problem): 
        zf = zipfile.ZipFile(self._fn)
        f = zipfile_stream(zf, zip_path_join(problem, 'problem.html'))
        statement = f.read()
        f.close()
        zf.close()
        template = _statement_template
        replacements = {
            '$TITLE': problem,
            '$STATEMENT': statement,
            '$VERSION': common.utils.version_number(),
        }
        for k, v in replacements.items():
            template = template.replace(k, v)
        return template

    def test_cases_for(self, problem):
        zf = zipfile.ZipFile(self._fn)
        f = zipfile_stream(zf, zip_path_join(problem, 'tests.txt'))
        res = read_run_file(problem, 'test', f)
        f.close()
        zf.close()
        return res

    def load_source(self, problem, source_name):
        zf = zipfile.ZipFile(self._fn)
        f = zipfile_stream(zf, zip_path_join(problem, source_name))
        src = f.read()
        f.close()
        zf.close()
        return src

    def load_object(self, problem, source_name):
        zf = zipfile.ZipFile(self._fn)
        f = zipfile_stream(zf, zip_path_join(problem, object_for(source_name)))
        compiled_code = lang.gbs_vm_serializer.load(f)
        f.close()
        zf.close()
        return compiled_code

    def load_board(self, problem, board_name):
        zf = zipfile.ZipFile(self._fn)
        fmt = lang.board.formats.format_for(board_name)
        board = lang.gbs_board.Board((1, 1))
        f = zipfile_stream(zf, board_name)
        board.load(f, fmt)
        f.close()
        zf.close()
        return board

    def global_fingerprint(self, problem):
        zf = zipfile.ZipFile(self._fn)
        f = zipfile_stream(zf, zip_path_join(problem, 'fingerprint.txt'))
        fgp = f.read()
        f.close()
        zf.close()
        return fgp

    def fingerprint_for_test_case(self, problem, test_case):
        zf = zipfile.ZipFile(self._fn)
        f = zipfile_stream(zf, zip_path_join(problem, 'fingerprint_%s.txt' % (test_case.id(),)))
        fgp = f.read()
        f.close()
        zf.close()
        return fgp

def compile_source(contents, fn='...', toplevel_filename=None, log=None):
    tree = lang.gbs_parser.parse_string_try_prelude(contents, filename=fn, toplevel_filename=toplevel_filename)
    lang.gbs_lint.lint(tree, strictness='lax')
    compiled_code = lang.gbs_compiler.compile_program(tree)
    return compiled_code

class CodeDictionary(object):
    def compiled_code_for(self, source_name):
        return self.code_dict[source_name]

class CodeDictionaryFromSolution(CodeDictionary):
    def __init__(self, bundle, problem, solution_source, fn='...', log=None):
        def log_(msg):
            if log is not None:
                log(msg)

        # Create the Solution.gbs file from the given source
        tmpdir = tempfile.mkdtemp()
        self._solution_filename = solution_filename = os.path.join(tmpdir, 'Solution.gbs')
        f = open(solution_filename, 'w')
        f.write(solution_source)
        f.close()

        # Copy the Prelude.gbs file to the test directory
        prelude_fn = lang.gbs_parser.prelude_for_file(fn)
        if prelude_fn is not None:
            shutil.copyfile(prelude_fn, os.path.join(tmpdir, os.path.basename(prelude_fn)))

        code_dict = {}
        for source_name in bundle.test_source_names(problem):
            if source_name != 'Solution.gbs':
                test_filename = os.path.join(tmpdir, source_name)
                test_source = bundle.load_source(problem, source_name)
                f = open(test_filename, 'w')
                f.write(test_source)
                f.close()
            else:
                test_filename = solution_filename
                test_source = solution_source
            try:
                compiled_code = compile_source(test_source, fn=test_filename, toplevel_filename=solution_filename, log=log_)
            except common.utils.SourceException as exception:
                shutil.rmtree(tmpdir)
                self.status = 'FAILED'
                self.exception = exception
                return
            code_dict[source_name] = compiled_code
        shutil.rmtree(tmpdir)

        self.status = 'OK'
        self.code_dict = code_dict

class CodeDictionaryFromObject(CodeDictionary):
    def __init__(self, bundle, problem):
        code_dict = {}
        self._solution_filename = '???'
        for source_name in bundle.test_source_names(problem):
            try:
                code_dict[source_name] = bundle.load_object(problem, source_name)
            except lang.gbs_vm_serializer.GbsObjectFormatException as exception:
                self.status = 'FAILED'
                self.exception = exception
                return
        self.status = 'OK'
        self.code_dict = code_dict

class TestDriver(object):
    def __init__(self, bundle, problem, code_dict, fn='...', log=None):
        self._bundle = bundle
        self._problem = problem
        self._code_dict = code_dict

        self._test_cases = self._bundle.test_cases_for(self._problem)
        self._state = 'start_test_case'
        self._current_test_case = 0
        self._solutions = {}
        self._log = log

    def problem(self):
        return self._problem

    def finished(self):
        return self._state == 'end'

    def log(self, msg):
        if self._log is not None:
            self._log(msg)

    def run(self):
        while True:
            r = self.step()
            if r == 'END':
                break
            elif r == 'FAILED':
                return 'FAILED'
        return 'OK'

    def step(self):
        if self._state == 'failed':
            return 'FAILED'
        elif self._state == 'start_test_case':
            return self.start_test_case(self._current_test_case)
        elif self._state == 'running':
            return self.step_vm()
        else:
            assert False

    def start_test_case(self, i):
        if i >= len(self._test_cases):
            self.log(i18n.i18n('Program execution finished.'))
            self._state = 'end'
            return 'END'
        n_of_m = ' (%s/%s)' % ((i + 1), len(self._test_cases))
        self.log(i18n.i18n('Starting test case %s.') % (self._test_cases[i].id(),) + n_of_m)

        compiled_code = self._code_dict.compiled_code_for(self._test_cases[i].program_name())
        self._test_board = self._bundle.load_board(self._problem, self._test_cases[i].board_name())

        try:
            self._vm = lang.gbs_vm.GbsVmInterpreter(toplevel_filename=self._code_dict._solution_filename)
            self._vm.init_program(compiled_code, self._test_board)
        except common.utils.SourceException as exception:
            self._error_exception = exception
            self._state = 'failed'
            return 'FAILED'
        self._state = 'running'
        return 'CONTINUE'

    def step_vm(self):
        try:
            r = self._vm.step()
            if r[0] == 'END':
                tc = self._test_cases[self._current_test_case]
                self._solutions[tc.id()] = (self._test_board, r[1])
                self._state = 'start_test_case'
                self._current_test_case += 1
                return 'CONTINUE'
            return 'CONTINUE'
        except common.utils.SourceException as exception:
            self._error_exception = exception
            self._state = 'failed'
            return 'FAILED'

    def solution(self, test_case):
        return self._solutions[test_case.id()]

    def current_test_case(self):
        return self._test_cases[self._current_test_case]

def solutions_equal(options, sol1, sol2):
    board1, keyval1 = sol1
    board2, keyval2 = sol2
    if options['check_board']:
        if not board1.equal_contents(board2):
            return False
    if options['check_head']:
        if board1.head != board2.head:
            return False
    if options['check_result']:
        if keyval1 != keyval2:
            return False
    return True

