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

import re

from gui.app import *

import common.utils
import common.position
import lang.judge.gbs_judge as gbs_judge
import lang.judge.report
import lang.bnf_parser

class JudgeGUI(GUI):

    def __init__(self, *args, **kwargs):
        self._current_problem = ''
        GUI.__init__(self, *args, **kwargs)

    def _menubar(self):
        mnu = []
        bundle_filenames = gbs_judge.collect_bundles()
        menubar = GUI._menubar(self)
        if bundle_filenames == []:
            return menubar
        self._problems = {}
        for fn in bundle_filenames:
            bundle = gbs_judge.GbzProblemBundle(fn)
            mnu.extend(self._build_submnu(bundle, bundle.problem_tree()))

        help_pos = menubar.index(i18n.i18n('&Help'))
        common.utils.seq_insert(menubar, help_pos, [
            i18n.i18n('&Problems'), mnu
        ])

        gobstones_menu_extension = [
            '--',
            i18n.i18n('&Solve problem'), (self.solve_problem_start_run, 'F12'),
        ]

        for i in range(len(menubar)):
            if menubar[i] != i18n.i18n('&Gobstones'): continue
            i += 1
            menubar[i].extend(gobstones_menu_extension)
            break
        return menubar

    def _build_submnu(self, curr_bundle, mnutree):
        submnu = []
        if isinstance(mnutree, list):
            sub2 = []
            for x in mnutree[1:]:
                sub2.extend(self._build_submnu(curr_bundle, x))
            submnu.extend([mnutree[0].strip('>'), sub2])
        else:
            p = mnutree
            self._problems[p] = curr_bundle
            submnu.extend([p, self.problem_statement_opener(p)])
        return submnu

    def problem_statement_opener(self, p):
        def opener(*args):
            contents = self._problems[p].problem_statement(p)
            common.utils.open_temp_html(p, contents)
        return opener

    def _search_problem_name(self):
        wsopt = '[ \t\r\n]*'
        ws = '[ \t\r\n]+'
        end_comment_opt = '("-}"|"*/")?'
        prfn = '(procedure|function)'
        ident = "([a-zA-Z][_a-zA-Z0-9']*)"
        problem_name = '@test' + wsopt + end_comment_opt + wsopt + prfn + ws + ident
        match = re.findall(problem_name, self.editor.current_text())
        if len(match) == 1 and len(match[0]) == 3:
            return match[0][2]
        elif len(match) > 1:
            self.show_string_error(i18n.i18n('Too many @test directives'))
            return None
        else:
            self.show_string_error(i18n.i18n('There is no valid @test directive'))
            return None

    def solve_problem_start_run(self, *args):
        if self._running:
            return
        self._running_start()

        p = self._search_problem_name()

        if p is None:
            return self._running_end()
        if p not in self._problems:
            self.show_string_error(i18n.i18n('Problem "%s" does not exist') % (p,))
            return self._running_end()
        self._current_problem = p

        run_reference = True
        if hasattr(self, '_ref_testdriver'):
            t = self._ref_testdriver
            if t is not None and t.problem() == p and t.finished():
                run_reference = False

        self.editor.clear_messages()
        self.editor.start_run(onstop=self.solve_problem_abort_run)
        self._run_log = self.editor.make_logger()
        self._run_log(i18n.i18n('Compiling.'))

        if not self._compile_usr_code():
            return self._running_end()
        
        if run_reference:
            if not self._compile_ref_code():
                return self._running_end()

        self._run_log(i18n.i18n('Starting problem %s') % (p,))

        self._drivers = []
        if run_reference:
            self._drivers.append(self._ref_testdriver)
        self._drivers.append(self._usr_testdriver)
        self._last_alarm_id = self.after(gui.config.TickDelay, self.solve_problem_continue_run)

    def _compile_usr_code(self):
        p = self._current_problem
        bundle = self._problems[p]
        usr_code_dict = gbs_judge.CodeDictionaryFromSolution(
            bundle, p,
            self.editor.current_text(),
            fn=self._filename_or_untitled(),
            log=self._run_log
        )
        if usr_code_dict.status == 'FAILED':
            exc = self._exception_wrap(usr_code_dict._solution_filename, usr_code_dict.exception)
            self.solve_problem_fail_run(exc)
            return False
        self._usr_testdriver = gbs_judge.TestDriver(
            bundle, p, usr_code_dict,
            fn=self._filename_or_untitled(),
            log=self._run_log
        )
        return True

    def _compile_ref_code(self):
        p = self._current_problem
        bundle = self._problems[p]
        ref_code_dict = gbs_judge.CodeDictionaryFromObject(bundle, p)
        if ref_code_dict.status == 'FAILED':
            self.show_string_error(ref_code_dict.exception)
            self.solve_problem_fail_run(exc)
            return False
        self._ref_testdriver = gbs_judge.TestDriver(
            bundle, p, ref_code_dict,
            fn=self._filename_or_untitled(),
            log=self._run_log
        )
        return True

    def solve_problem_continue_run(self):
        if not self._running:
            return
        if len(self._drivers) == 0:
            return self.solve_problem_end_run()

        driver = self._drivers[0]
        for i in range(gui.config.IterationsPerTick):
            if not self._running:
                return
            result = driver.step()
            if result == 'END':
                self._drivers.pop(0)
                break
            elif result == 'FAILED':
                self._solve_problem_fail()
                return
        self._last_alarm_id = self.after(gui.config.TickDelay, self.solve_problem_continue_run)

    def problem_options(self):
        p = self._current_problem
        return self._problems[p].options(p)

    def _exception_wrap(self, solution_filename, exception):
        if exception.area.filename() == solution_filename:
            return exception
        else:
            return SourceException(exception.msg, lang.bnf_parser.fake_bof())

    def _solve_problem_fail(self):
        options = self.problem_options()
        if options['provide_counterexample']:
            exc = self._exception_wrap(
                self._usr_testdriver._code_dict._solution_filename,
                self._usr_testdriver._error_exception
            )
            p = self._current_problem
            bundle = self._problems[p]
            tc = self._usr_testdriver.current_test_case()

            initial_board = bundle.load_board(p, tc.board_name())
            if tc.program_name() == 'Solution.gbs':
                test_source_code = None
            else:
                test_source_code = bundle.load_source(p, tc.program_name())
            ref_sol = self._ref_testdriver.solution(tc)
            self.solve_problem_fail_run(exc)
            lang.judge.report.FailedTestReport(
                    options, p, tc, initial_board, test_source_code, ref_sol, None).display()
        else:
            self.solve_problem_fail_run(
                SourceException(i18n.i18n('Runtime error. Debug program and retry.'),
                                                lang.bnf_parser.fake_bof()))

    def solve_problem_abort_run(self):
        self._ref_testdriver = None
        self._usr_testdriver = None
        self.solve_problem_fail_run(
            SourceException(i18n.i18n('Execution interrupted by the user'),
            lang.bnf_parser.fake_bof()))

    def solve_problem_fail_run(self, exception):
        self._ref_testdriver = None
        self._usr_testdriver = None
        self.editor.end_run()
        self.editor.show_error(exception)
        self._running_end()

    def solve_problem_end_run(self):
        self.check_results()

        # Do NOT set it to None, to allow caching the
        # reference results
        #self._ref_testdriver = None

        self._usr_testdriver = None
        self.editor.end_run()
        self._running_end()

    def check_results(self):
        options = self.problem_options()
        if options['provide_counterexample']:
            self.check_fingerprints_with_counterexample(with_result=options['provide_expected_result'])
        else:
            self.check_fingerprints_silent()

    def check_fingerprints_with_counterexample(self, with_result=False):
        self._run_log(i18n.i18n('Checking fingerprints'))
        p = self._current_problem
        bundle = self._problems[p]
        i = 0
        for tc in bundle.test_cases_for(p):
            i += 1

            ref_sol = self._ref_testdriver.solution(tc)
            usr_sol = self._usr_testdriver.solution(tc)
            if not gbs_judge.solutions_equal(self.problem_options(), ref_sol, usr_sol):
                self.editor.show_raw_error(
                    i18n.i18n('Program failed on test case "%s". Debug program and retry.') % (tc.run_name(),))

                initial_board = bundle.load_board(p, tc.board_name())
                if tc.program_name() == 'Solution.gbs':
                    test_source_code = None
                else:
                    test_source_code = bundle.load_source(p, tc.program_name())

                if not with_result:
                    ref_sol = None
                lang.judge.report.FailedTestReport(
                        self.problem_options(), p, tc,
                        initial_board, test_source_code, ref_sol, usr_sol).display()
                return
        self.editor.show_check_ok(i18n.i18n('Program solving problem "%s" was accepted by judge') % (p,))

    def check_fingerprints_silent(self):
        self._run_log(i18n.i18n('Checking fingerprints'))
        p = self._current_problem
        bundle = self._problems[p]
        i = 0
        for tc in bundle.test_cases_for(p):
            i += 1
            ref_sol = self._ref_testdriver.solution(tc)
            usr_sol = self._usr_testdriver.solution(tc)
            if not gbs_judge.solutions_equal(self.problem_options(), ref_sol, usr_sol):
                self.editor.show_raw_error(
                    i18n.i18n('Program failed on some test cases. Debug program and retry.'))
                return
        self.editor.show_check_ok(i18n.i18n('Program solving problem "%s" was accepted by judge') % (p,))

#    self._run_log(i18n.i18n('Checking fingerprints'))
#    p = self._current_problem
#    bundle = self._problems[p]
#    ref_fgp = bundle.global_fingerprint(p)
#    usr_fgp = self._run_testdriver.fingerprint()
#    if ref_fgp != usr_fgp:
#      self.editor.show_raw_error(
#        i18n.i18n('Program failed on some test cases. Debug program and retry.'))
#    else:
#      self.editor.show_check_ok(i18n.i18n('Program solving problem "%s" was accepted by judge') % (p,))

