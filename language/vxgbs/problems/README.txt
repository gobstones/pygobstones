Directory contents:

  src/
    The problems, as written by the problem setter.
    It should contain a file "Solution.gbs" with source code
    for solving the problem in question.

  gbz.py
    This tool takes "source" problems and generates a .gbz bundle.

    The .gbz bundle contains the problems, as seen by the problem solver.
    Instead of containing solutions to the problems, it has "fingerprints",
    which are basically:
        hash(run(solution, test_case))
    for each test case.

----

Life-cycle of a problem:

(1) To create a new problem, make a directory <path>/<problem_id>/
    It should contain:
  
    - A file, "problem_type.txt", specifying the type of problem
      we're dealing with. For instance, it could be a problem where
      the contents of the board do not matter, but the values
      of the variables returned from the Main procedure do.
  
    - A "problem.html" document stating the problem.
  
    - A "Solution.gbs" program, the official solution.
  
    - A "tests.txt" files, describing the test cases, one per line.
      A test case consists of a program plus an input board.
      For instance:

$ cat <path>/<problem>/tests.txt
Test1.gbs Board1a.gbb
Test1.gbs Board1b.gbb
Test2.gbs Board2.gbb

      The script src/tcgen.py may aid in
      creating random *.gbb boards.

(2) Create a problem set file. It consists of a title in the
    first line, and a list of problems in each of the next lines.
    For instance:

$ cat <path>/exercise_guide1.txt
>Exercise Guide 1 - Introduction
problem1
problem2
problem3

(3) Run "./gbz.py <path>/exercise_guide1.txt" to generate
    the bundle "exercise_guide1.gbz".

(4) Put the .gbz bundle in the PyGobstones installation path
    (or in the problems/ subdirectory). The Gobstones GUI
    should automatically load it.

