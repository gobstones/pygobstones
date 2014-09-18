import itertools
import functools
from test import TestCase, GobstonesTest, run_gobstones
import math

def ifloor(f):
    return int(math.floor(f))

def iceil(f):
    return int(math.ceil(f))

def read_file(fn):
    f = open(fn, 'r')
    s = f.read()
    f.close()
    return s

def write_file(fn, s):
    f = open(fn, "w")
    f.write(s)
    f.close()
    
def copy_file(fn, fnnew):
    write_file(fnnew, read_file(fn))

def temp_test_file(codestr):
    fn = "./examples/" + str(id(codestr)) + ".gbs"
    write_file(fn, codestr)
    return fn
    
def unzip(l):
    return [list(t) for t in zip(*l)]

def group(lst, n):
    res = []
    sublst = []
    for x in lst:
      sublst.append(x)
      if len(sublst) == n:
          res.append(sublst)
          sublst = []
    if len(sublst) > 0:
        res.append(sublst)
    return res

def flatten(lst):
    res = []
    for x in lst:
        if isinstance(x, list):
            res.extend(flatten(x))
        else:
            res.append(x)
    return res


def nats(start, end):
    if (start < end):
        return list(range(start, end+1))
    else:
        l = list(range(end, start+1))
        l.reverse()
        return l
    
BINOPS = {
    "+": lambda x, y: x + y,
    "-": lambda x, y: x - y,
    "*": lambda x, y: x * y,
    "div": lambda x, y: x / y,
    "mod": lambda x, y: x % y,
}
    
binop = lambda op, x, y: BINOPS[op](x,y)

# Gbs syntax

isNil = lambda xs: len(xs) == 0
head = lambda xs: xs[0]
tail = lambda xs: xs[1:]

# Test scripts

def combine_args(args):
    prod = itertools.product(*args.values())
    return [dict(zip(args.keys(),pargs)) for pargs in prod]    
    
class Operation(object):
  def __init__(self, nretvals, code, replace={}):
    self.nretvals = nretvals
    for k, v in replace.items():
      code = code.replace('@' + k, str(v))
    self.code = code
    
class TestScript(object):
    
    def __init__(self, possible_args):
        self.cases = combine_args(possible_args)
    
    def build_tests(self):
        return [self.build_test(c) for c in self.cases]
    
    def build_test(self, args):
        return (Operation(self.nretvals(), self.gbs_code(), args), self.py_func(args))
    
    def nretvals(self):
        return 1
    
    def gbs_code(self):
        return "Skip"
    
    def py_func(self, args):
        return functools.partial(self.pyresult, args)
    
    def py_code(self, args):
        pass
    
# Tests

class TestForeachWithRangeIterations(TestScript):
    
    def __init__(self):
        super(TestForeachWithRangeIterations, self).__init__({"start_val": [1, 7, 11,21], "end_val": [21,5,13]})
    
    def gbs_code(self):
        return '''
            VaciarTablero()
            foreach i in [@start_val..@end_val] {
                Poner(Verde)
            }
            return(nroBolitas(Verde))
        '''
    
    def pyresult(self, args):
        start = args["start_val"]
        end = args["end_val"]
        if start <= end:
            return end+1 - start
        else:
            return 0
        
class TestForeachWithRangeAndDeltaIterations(TestScript):
     
    def __init__(self):
        super(TestForeachWithRangeAndDeltaIterations, self).__init__({"start_val": [0, 7, 11,21], "end_val": [21,5,13], "delta": [1,-1,2,-2,3,-3]})
     
    def gbs_code(self):
        return '''
            VaciarTablero()
            foreach i in [@start_val, @start_val + @delta ..@end_val] {                
                Poner(Verde)
            }
            return(nroBolitas(Verde))
        '''
     
    def pyresult(self, args):
        start = args["start_val"]
        end = args["end_val"]
        delta = args["delta"] * 1.0
        if start == end:
            return 1
        if delta > 0 and start > end:
            return 0            
        elif delta < 0 and end > start:
            return 0        
        elif start <= end:
            return iceil((end+1 - start)/abs(delta))
        else:
            return iceil((start+1 - end)/abs(delta))
            
    
TESTS_GROUPS = group(flatten([cls().build_tests() for cls in TestScript.__subclasses__()]), 128)

def program_for(exprs):
  variables = []
  def expr_eval(i, e):
    if isinstance(e, Operation):
      if e.nretvals == 1: 
        variables.append('x_%i' % (i,))
        return 'x_%i := f0_%i()' % (i, i,)
      else:
        vs = ['x_%i_%i' % (i, j) for j in range(e.nretvals)]
        variables.extend(vs)
        return '(%s) := f0_%i()' % (','.join(vs), i,)
    else:
      variables.append('x_%i' % (i,))
      return 'x_%i := %s' % (i, e)
  R = range(len(exprs))
  prog = []
  for i, e in zip(R, exprs):
    if isinstance(e, Operation):
      prog.append('function f0_%i() {' % (i,))
      prog.append(e.code)
      prog.append('}')
  prog.append('program {')
  prog.append(''.join(['  %s\n' % (expr_eval(i, e),) for i, e in zip(R, exprs)]))
  prog.append('  return (%s)\n' % (', '.join(variables),))
  prog.append('}\n')
  return '\n'.join(prog)


def eqValue(gbsv, pyv):
    return gbsv == str(pyv)


class AutoGobstonesTest(GobstonesTest):

    def __init__(self, gbscode, pyfuncs):
        self.gbscode = gbscode
        self.pyfuncs = pyfuncs
        
    def run(self):
        testres = {"passed": 0, "failed": 0, "errors": 0, "total": 0}
        results = run_gobstones(temp_test_file(self.gbscode), "./boards/empty.gbb")
        if results[0] == "OK":
            gbsres = results[1]
            pyres = []
            for f in self.pyfuncs:
                pyr = f()
                if isinstance(pyr, tuple):
                    pyres += list(pyr)
                else:
                    pyres.append(pyr)
                    
            if len(pyres) == len(gbsres):
                for gbsval, pyval in zip(unzip(gbsres)[1], pyres):
                    testres['total'] += 1
                    if eqValue(gbsval, pyval):
                        testres['passed'] += 1
                    else: 
                        testres['failed'] += 1
                        
                return tuple(testres.values())
            else:
                return (0,0,1,1)            
        else:
            return (0,0,1,1)
        

class AutoTestCase(TestCase):
    
    def __init__(self):
        super(AutoTestCase, self).__init__("AutoTestCase")
        copy_file("./autotests/Biblioteca.gbs", "./examples/Biblioteca.gbs")
    
    def get_gobstones_tests(self):
        tests = []
        for tgroup in TESTS_GROUPS:
            ops, pyfs = unzip(tgroup) 
            tests.append(AutoGobstonesTest(program_for(ops), pyfs))
        return tests        
 