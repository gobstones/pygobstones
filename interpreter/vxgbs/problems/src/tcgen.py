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
sys.path.append('../../')

import os
import random
import imp

import common.utils
import lang.judge
import lang.judge.gbs_judge as gbs_judge
import lang.board.formats
import lang.gbs_board
import lang.bnf_parser
import lang.gbs_parser
import lang.gbs_lint
import lang.gbs_compiler
import lang.gbs_vm
import lang.gbs_builtins
import lang.gbs_board

def report_error(errtype, msg):
  sys.stderr.write('%s:\n' % (errtype,))
  sys.stderr.write('%s\n' % (common.utils.indent(msg),))

def report_program_error(exception):
  sys.stderr.write('\n%s\n' % (exception.area,))
  report_error(exception.error_type(), exception.msg)

def pad(n, padlen):
  s = str(n)
  if len(s) >= padlen:
    return s
  else:
    return (padlen - len(s)) * '0' + s

def all_lists(values, n):
  if n == 0:
    yield []
  else:
    for v in values:
      for vs in all_lists(values, n - 1):
        yield [v] + vs

def standard_boards(size_str):
  def rg(x):
    if '..' in x:
      l, u = x.split('..')
      return range(int(l), int(u) + 1)
    else:
      return [int(x)]
  def generate_start_pos_point():
    as_ = ['start', 'mid', 'end']
    bs_ = ['start', 'mid', 'end']
    for a in as_:
      for b in bs_:
        yield a, b
  def start_pos_from_point(points, size):
    def p(point, x):
      if point == 'start':
        return 0
      elif point == 'end':
        return x - 1
      elif point == 'mid':
        return x / 2
    return p(points[1], size[1]), p(points[0], size[0])
  def generate_size():
    W, H = size_str.split('x')
    szs = []
    for w in rg(W):
      for h in rg(H):
        szs.append((w, h))
    for x in szs:
      yield x
  def empty(board):
    b.clear_board()
  def fill(num_a, num_n, num_r, num_v):
    num_per_col = [num_a, num_n, num_r, num_v]
    def f(board):
      w, h = board.size
      b.clear_board()
      for x in range(w):
        for y in range(h):
          board.head = (y, x)
          for i in range(4):
            for num in range(num_per_col[i]):
              board.put_stone(lang.gbs_builtins.Color(i))
    return f
  def put(num_a, num_n, num_r, num_v):
    num_per_col = [num_a, num_n, num_r, num_v]
    def f(board):
      b.clear_board()
      for i in range(4):
        for num in range(num_per_col[i]):
          board.put_stone(lang.gbs_builtins.Color(i))
    return f
  def fill_neighbours(full_xneso, colors):
    def f(board):
      b.clear_board()
      board.put_stone(colors[0])
      i = 0
      for d in [lang.gbs_builtins.Direction(i) for i in [0, 1, 2, 3]]:
        i += 1
        if board.can_move(d):
          board.move(d)
          board.put_stone(colors[i])
          board.move(d.opposite())
    return f
  def generate_actions():
    actions = [empty]
    for lst in all_lists([0, 1, 10], 4):
      actions.append(fill(*lst))
      actions.append(put(*lst))
    cycle = [lang.gbs_builtins.Color(i) for i in [0, 1, 2, 3]]
    for lst in all_lists([False, True], 5):
      actions.append(fill_neighbours(lst, (cycle + cycle)[:5]))
      cycle.append(cycle.pop(0))
    for x in actions:
      yield x
  start_pos_point_gen = generate_start_pos_point()
  size_gen = generate_size()
  for action in generate_actions():
    try:
      start_pos_point = next(start_pos_point_gen)
    except StopIteration:
      start_pos_point_gen = generate_start_pos_point()
    try:
      size = next(size_gen)
    except StopIteration:
      size_gen = generate_size()

    start_pos = start_pos_from_point(start_pos_point, size)
    b = lang.gbs_board.Board(size)
    b.head = start_pos
    action(b)
    b.head = start_pos
    yield b

def randboard(size):
  def rg(x):
    if '..' in x:
      l, u = x.split('..')
      return random.randint(int(l), int(u))
    else:
      return int(x)
  W, H = size.split('x')
  b = lang.gbs_board.Board((rg(W), rg(H)))
  b.randomize()
  return b

def board_generator(size):
  while True:
    yield randboard(size)

def is_board(fn):
  for fmt in ['.gbt', '.gbb']:
    if fn.endswith(fmt):
      return True
  return False

def interp_ok(s, board_fn=None, board_0=None):
  try:
    tree = lang.gbs_parser.parse_file(s)
    lang.gbs_lint.lint(tree, strictness='lax')
    compiled_code = lang.gbs_compiler.compile_program(tree)
  except common.utils.SourceException as exception:
    report_program_error(exception)
    sys.exit(1)

  try:
    board = lang.gbs_board.Board((1, 1))
    if board_0 is None:
      fmt = board_fn[-3:]
      f = open(board_fn, 'r')
      board.load(f, fmt)
      f.close()
    else:
      board.clone_from(board_0)
    res = lang.gbs_vm.interp(compiled_code, board)
    return True
  except common.utils.SourceException as exception:
    return False

def read_sources(problem):
  sources = []
  for fn in os.listdir(problem):
    if fn.endswith('.gbs'):
      sources.append(fn)
  sources.sort()
  if 'Solution.gbs' not in sources:
    sys.stderr.write('There is no Solution.gbs\n')
    sys.exit(1)
  return sources

def read_boards(problem):
  boards = []
  for fn in os.listdir(problem):
    if is_board(fn):
      boards.append(fn)
  boards.sort()
  return boards

def validate_boards(problem):
  sys.stderr.write('validating boards\n')
  sources = read_sources(problem)
  if len(sources) > 1:
    sources.remove('Solution.gbs')

  test_out = open(os.path.join(problem, 'tests.txt'), 'w')
  boards = read_boards(problem)
  for s in sources:
    for board_fn in boards:
      if interp_ok(os.path.join(problem, s), board_fn=os.path.join(problem, board_fn)):
        print(s, board_fn)
        test_out.write('%s %s/%s\n' % (s, problem, board_fn))
  test_out.close()

def gen_boards(problem, n, sz):
  sys.stderr.write('generating random boards\n')
  padlen = len(str(n))
  for i in range(n):
    b = randboard(sz)
    f = open(os.path.join(problem, 'RandBoard%s.gbb' % (pad(i + 1, padlen),)), 'w')
    b.dump(f, 'gbb', style='compact')
    f.close()

def gen_standard_boards(problem, size):
  sys.stderr.write('generating standard boards\n')
  i = 0
  for b in standard_boards(size):
    i += 1
    f = open(os.path.join(problem, 'StdBoard%s.gbb' % (pad(i, 3),)), 'w')
    b.dump(f, 'gbb', style='compact')
    f.close()

def common_board_contents():
  boards = os.listdir('_boards')
  for b_fn in common.utils.seq_sorted(boards):
    # do not use os.path.join, since this will end up
    # in a zipfile
    yield '_boards/' + b_fn

def gen_valid_boards(problem, n, sz):
  sys.stderr.write('generating valid test case boards\n')
  sources = read_sources(problem)
  if len(sources) > 1:
    sources.remove('Solution.gbs')

  padlen = len(str(n))

  test_out = open(os.path.join(problem, 'tests.txt'), 'w')

  def interp_board(board_fn, board_0=None):
    board_useful = False
    for s in sources:
      if board_0 is None:
        fn2 = board_fn
      else:
        fn2 = None
      if interp_ok(os.path.join(problem, s), board_fn=fn2, board_0=board_0):
        board_useful = True
        print(s, board_fn)
        test_out.write('%s %s\n' % (s, board_fn.replace('\\', '/')))
    return board_useful

  def generate_fixed_boards():
    for board_fn in read_boards(problem):
      if board_fn.startswith('RandBoard') or board_fn.startswith('AutoBoard'):
        continue
      interp_board(os.path.join(problem, board_fn))

  def generate_standard_boards():
    i = 0
    board_fns = []
    for board_fn in common_board_contents():
      board_fns.append(board_fn)
    random.shuffle(board_fns)
    for board_fn in board_fns:
      board_useful = interp_board(board_fn)
      if board_useful:
        i += 1
        if i == n:
          break

  def generate_auto_boards():
    modname = os.path.join(problem, 'autogen.py')
    i = 1
    if os.path.exists(modname):
      autogen = imp.load_source('autogen_%s' % (problem,), modname)
      autogen.Board = lang.gbs_board.Board
      padlen = 2
      for b in autogen.gen():
        board_fn = 'AutoBoard%s.gbb' % (pad(i, padlen),)
        board_useful = interp_board(os.path.join(problem, board_fn), board_0=b)
        if board_useful:
          f = open(os.path.join(problem, board_fn), 'w')
          b.dump(f, 'gbb', style='compact')
          f.close()
          i += 1
        else:
          sys.stderr.write('Useless board\n')
    else:
      generate_random_boards()

  def generate_random_boards():
    gen = board_generator(sz)
    i = 1
    while i <= n:
      b = next(gen)
      board_fn = 'RandBoard%s.gbb' % (pad(i, padlen),)
      board_useful = interp_board(os.path.join(problem, board_fn), board_0=b)
      if board_useful:
        f = open(os.path.join(problem, board_fn), 'w')
        b.dump(f, 'gbb', style='compact')
        f.close()
        i += 1
      else:
        sys.stderr.write('Useless board\n')
    test_out.close()

  generate_fixed_boards()
  generate_auto_boards()
  #generate_standard_boards()
  #generate_random_boards()

def clean_problem(problem):
  sys.stderr.write('Cleaning problem %s\n' % (problem,))
  for fn in os.listdir(problem):
    if fn.startswith('RandBoard') and fn.endswith('.gbb'):
      os.remove(os.path.join(problem, fn))
    if fn.startswith('AutoBoard') and fn.endswith('.gbb'):
      os.remove(os.path.join(problem, fn))
    if fn.endswith('.pyc'):
      os.remove(os.path.join(problem, fn))
  fn = os.path.join(problem, 'tests.txt')
  # empty file
  f = open(fn, 'w')
  f.close()

def usage():
  sys.stderr.write('Usage: %s [options] problem_name\n' % (sys.argv[0],))
  sys.stderr.write('       %s [options] --set problem_set.txt\n' % (sys.argv[0],))
  sys.stderr.write('Recommended usages:\n')
  sys.stderr.write('    %s problem_name --valid --gen 10\n' % (sys.argv[0],))
  sys.stderr.write('    %s --set PracticaN.txt --valid --gen 10\n' % (sys.argv[0],))
  sys.stderr.write('Options:\n')
  sys.stderr.write('  --valid\n')
  sys.stderr.write('    print all the pairs:\n')
  sys.stderr.write('        program board\n')
  sys.stderr.write('    that yield a valid solution\n')
  sys.stderr.write('    Search for the source in <problem_name>/\n')
  sys.stderr.write('    Search for the boards in <problem_name>/\n')
  sys.stderr.write('    or randomly generate them if the --gen option is used.\n')
  sys.stderr.write('  --std\n')
  sys.stderr.write('    generate the "standard" set of boards\n')
  sys.stderr.write('  --gen N\n')
  sys.stderr.write('    randomly generate N boards and save them in problem_name/\n')
  sys.stderr.write('  --size WxH\n')
  sys.stderr.write('    the generated boards are of size WxH.')
  sys.stderr.write('    The dimensions can be numbers or ranges.\n')
  sys.stderr.write('    For instance,\n')
  sys.stderr.write('        5x1..9\n')
  sys.stderr.write('    generates a board 5 cells wide and\n')
  sys.stderr.write('    random.randint(1,9) cells high.\n')
  sys.stderr.write('  --clean\n')
  sys.stderr.write('    clean random boards (RandBoard.*)\n')
  sys.exit(1)

def main():
  option_switches = [
    '--valid',
    '--gen X',
    '--size X',
    '--std',
    '--set X',
    '--clean'
  ]
  options = common.utils.parse_options(option_switches, sys.argv, max_args=1)
  if not options: usage()
  arguments, opt = options

  if opt['set'] != []:
    f = open(opt['set'][0], 'r')
    problems = gbs_judge.problem_tree_to_list(gbs_judge.read_problem_tree(f))
    f.close()
  else:
    if len(arguments) != 1: usage()
    problems = [arguments[0]]

  for problem in problems:
    if problem[-1] == '/':
      problem = problem[:-1]

    if opt['clean']:
      clean_problem(problem) 
      continue

    if opt['size'] != [] and not opt['gen'] and not opt['std']:
      opt['gen'] = ['1']

    if opt['size'] == []:
      opt['size'] = ['9x9']

    if opt['valid'] and opt['gen']:
      number = int(opt['gen'][0])
      sz = opt['size'][0]
      clean_problem(problem) 
      gen_valid_boards(problem, number, sz)
    elif opt['valid']:
      clean_problem(problem) 
      validate_boards(problem)
    elif opt['gen']:
      number = int(opt['gen'][0])
      sz = opt['size'][0]
      clean_problem(problem) 
      gen_boards(problem, number, sz)
    elif opt['std']:
      sz = opt['size'][0]
      gen_standard_boards(problem, sz)
    else:
      usage()

if __name__ == '__main__':
  main()

