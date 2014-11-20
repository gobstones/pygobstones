import itertools
import random
import functools
from test_logger import log
from test import TestCase, GobstonesTest, run_gobstones

randint = lambda x: random.randint(0,x-1)

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

def randomList(generator, max_size=16):
    return [generator(i) for i in range(randint(max_size) + 4)]

def randomIntList(max_size=16, max_number=99):
    return randomList(lambda i: randint(max_number), max_size)

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
    
COLORS = ["Azul", "Negro", "Rojo", "Verde"]
DIRS = ["Norte", "Este", "Sur", "Oeste"]
BOOLS = ["True", "False"]
    
BINOPS = {
    "+": lambda x, y: x + y,
    "-": lambda x, y: x - y,
    "*": lambda x, y: x * y,
    "div": lambda x, y: x / y,
    "mod": lambda x, y: x % y,
}
    
binop = lambda op, x, y: BINOPS[op](x,y)

# Gbs syntax

isEmpty = lambda xs: len(xs) == 0
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
    
class TestScript(GobstonesTest):
    
    def __init__(self, possible_args):
        self.cases = combine_args(possible_args)
    
    def name(self):
        return self.__class__.__name__
    
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

class TestOpMapping(TestScript):

    def __init__(self):
        super(TestOpMapping, self).__init__({"length": [5,10,20], "operation": BINOPS.keys()})
        
    def gbs_code(self):
        return '''
            xs := nats(1, @length)
            ys := nats(@length, 1)
            zs := []
            while(not isEmpty(xs)) {
                zs := zs ++ [head(xs) @operation head(ys)]
                xs := tail(xs)
                ys := tail(ys)
            }
            return(zs)
        '''    
        
    def pyresult(self, args):
        xs = nats(1, args["length"])
        ys = nats(args["length"], 1)
        zs = []
        while (not isEmpty(xs)):
            zs = zs + [binop(args["operation"], head(xs), head(ys))]
            xs = tail(xs)
            ys = tail(ys)
        return zs
    

class TestOpInject(TestScript):
    
    def __init__(self):
        super(TestOpInject, self).__init__({"length": [5,10,20], "operation": BINOPS.keys()})
    
    def gbs_code(self):
        return '''
            xs := nats(1, @length)
            ys := nats(@length, 1)
            res := 0
            while(not isEmpty(xs)) {
                res := res + (head(xs) @operation head(ys))
                xs := tail(xs)
                ys := tail(ys)
            }
            return(res)
        '''
        
    def pyresult(self, args):
        xs = nats(1, args["length"])
        ys = nats(args["length"], 1)
        res = 0
        while (not isEmpty(xs)):
            res += binop(args["operation"], head(xs), head(ys))
            xs = tail(xs)
            ys = tail(ys)
        return res
    
    
class TestEnumeration(TestScript):
    def __init__(self):
        super(TestEnumeration, self).__init__({"list": self.generate_cases(20)})
        
    def generate_cases(self, n):
        types = [COLORS, DIRS, BOOLS]

        def gen_case():
            vals = types[randint(len(types))]            
            return [vals[randint(len(vals))] for _ in range(randint(16) + 4)]  
        
        cases = []
        for _ in range(n):
            cases += ["[%s]" % (", ".join(gen_case()),)]
        return cases
        
    def nretvals(self):
        return 1
        
    def gbs_code(self):
        return '''
            last := head(@list)
            first_ocurr := 0
            foreach i in @list {
                if (i == last) {
                    first_ocurr := first_ocurr + 1
                }
            }
            return(first_ocurr)
        '''
        
    def pyresult(self, args):
        vals = args["list"][1:-1].split(", ")
        return vals.count(vals[0])

    
class TestListGenerator(TestScript):
    def __init__(self):
        super(TestListGenerator, self).__init__({"low": [1, 11, 33], "high": [11, 51, 22]})
    
    def nretvals(self):
        return 7
    
    def gbs_code(self):
        return '''
            xs := [@low..@high]
            ys := [@low,@low+1..@high]
            zs := [@high,@high-1..@low]
            ws := [@low,@low+5..@high]
            vs := [@high, @high-5..@low]
            us := [@low,@low+9..@high]
            ts := [@high, @high-9..@low]            
            return(ts, us, vs, ws, xs, ys, zs)
        '''
        
    def pyresult(self, args):
        xs = range(args['low'], args['high']+1)
        ys = range(args['low'], args['high']+1, 1)
        zs = range(args['high'], args['low']-1, -1)
        ws = range(args['low'], args['high']+1, 5)
        vs = range(args['high'], args['low']-1, -5)
        us = range(args['low'], args['high']+1, 9)
        ts = range(args['high'], args['low']-1, -9)
        return ts, us, vs, ws, xs, ys, zs
    
    
    
class TestRepeat(TestScript):
    def __init__(self):
        super(TestRepeat, self).__init__({"times": randomIntList(5, 20)})
    
    def nretvals(self):
        return 1
    
    def gbs_code(self):
        return '''
            count := 0
            repeat (@times)
             { count := count + 1 }
            return(count)
        '''
        
    def pyresult(self, args):
        return args["times"]
    
    
    
class TestForeachSeq(TestScript):
    def __init__(self):
        numbers = randomList(lambda i: "[" + ",".join(map(str, randomIntList(10))) + "]", 5)
        super(TestForeachSeq, self).__init__({"numbers": numbers})
    
    def nretvals(self):
        return 1
    
    def gbs_code(self):
        return '''
            res := 0
            foreach n in @numbers
             { res := res*10 + n }
            return(res)
        '''
        
    def pyresult(self, args):
        res = 0
        ns = args["numbers"][1:-1].split(",")
        for n in map(int, ns):
            res = res*10 + n
        return res 
    
    
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
    prog.append('t.program {')
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
                    if not eqValue(gbsval, pyval):
                        return "FAILED"
                return "PASSED"
            else:
                return "FAILED"            
        else:
            return results[0]
        

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
 