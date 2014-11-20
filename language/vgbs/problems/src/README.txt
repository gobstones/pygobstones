
-- Set of files needed to create a problem

problem.html

  Problem statement in HTML.

problem_type.txt

  Defines four boolean values that determine how the judge behaves
  when comparing the reference solution with the target solution:

    check_board
      Compare the contents of the board, distinguishing the number of
      stones of each color in each cell.

    check_head
      Compare the final position of the head in the board.

    check_result
      Compare the values of the variables returned by the program in
      the Main procedure.

    provide_counterexample
      Allow the judge to provide a failed test case in presence
      of a wrong answer.

    provide_expected_result
      Provide also the expected result when showing a counterexample.

Solution.gbs

  Reference solution.

tests.txt

  Test cases. The reference solution is compared
  with the target solution using these test cases.

  Each line is of the form:
    <program-file> <board-file>

  <program-file> should be an existing .gbs file.
  <board-file> should be an existing board file, in any of
  the allowed formats (for instance, "Board1.gbt").

--

There are two possible kinds of tests cases:

(1) Run the Main procedure of the Solution.

    In that case, <program-file> should be "Solution.gbs"

(2) Run a specific Main procedure, suited for this test case
    (using procedures or functions defined in Solution.gbs).

    In that case, <program-file> can be any filename.

    For instance, if the problem required the user to
    write a procedure called "FillBoard", we would have
    something like:

    -- Solution.gbs 
      procedure FillBoard()
      {
        ...
      }
      ...

    -- Test1.gbs
      from Solution import (FillBoard)

      procedure Main()
      {
        ...FillBoard()...
      }

    -- tests.txt
      ...
      Test1.gbs Board1a.gbb
      Test1.gbs Board1b.gbb
      ...

