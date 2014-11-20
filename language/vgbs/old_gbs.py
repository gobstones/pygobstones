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

import os
import sys

import common.i18n as i18n
import common.utils
import lang.bnf_parser
import lang.gbs_parser
import lang.gbs_lint
import lang.gbs_liveness
import lang.gbs_infer
import lang.gbs_compiler
import lang.gbs_vm
import lang.gbs_vm_serializer
import lang.gbs_builtins
import lang.gbs_pprint
import lang.gbs_board
import lang.board.formats
import lang.jit.gbs_jit

def report_error(errtype, msg):
    sys.stderr.write('%s:\n' % (errtype,))
    sys.stderr.write('%s\n' % (common.utils.indent(msg),))

def report_program_error(errtype, msg, area):
    sys.stderr.write('\n%s\n' % (area,))
    report_error(errtype, msg)

def run_filename(fn, **options):
    if not os.path.exists(fn):
        report_error(i18n.i18n('Error'), i18n.i18n('File %s does not exist') % (fn,))
        return False

    lfn = fn.lower()
    if lfn.endswith('.gbo'):
        return run_object_filename(fn, **options)
    elif lang.board.formats.is_board_filename(fn):
        return run_board_filename(fn, **options)
    else:
        return run_gbs_filename(fn, **options)

def style(options):
    if options['style']:
        style = options['style'][0]
    else:
        style = 'verbose'
    return style

def run_board_filename(fn, **options):
    b = lang.gbs_board.load_board_from(fn)
    if options['print-board']:
        print(b)
    if options['to']:
        lang.gbs_board.dump_board_to(b, options['to'], style=style(options))
    return True

def make_runnable(compiled_code, **options):
    if options['jit']:
        runnable = lang.jit.gbs_jit.JitCompiledRunnable(compiled_code)
        if options['print-jit']:
            print(runnable.jit_code())
        if options['print-native']:
            print('## Native code')
            print(runnable.native_code())
            print('## End of native code')
    else:
        runnable = lang.gbs_vm.VmCompiledRunnable(compiled_code)
    return runnable

def run_object_filename(fn, **options):
    f = open(fn, 'r')
    compiled_code = lang.gbs_vm_serializer.load(f)
    f.close()
    if options['print-asm']:
        print(compiled_code)
        return True
    runnable = make_runnable(compiled_code, **options)
    return run_runnable(runnable, **options)

def run_gbs_filename(fn, **options):
    try:
        # parse
        tree = lang.gbs_parser.parse_file(fn)
        # lint
        lang.gbs_lint.lint(tree, strictness=options['lint'])
        # liveness check
        if options['liveness']:
            lang.gbs_liveness.check_live_variables(tree)
        # type checking
        if options['typecheck']:
            lang.gbs_infer.typecheck(tree)

        if options['print-ast']:
            print(tree.show_ast(show_liveness=False))
            return True

        if options['pprint']:
            print(lang.gbs_pprint.pretty_print(tree))
            return True

        # compiler
        compiled_code = lang.gbs_compiler.compile_program(tree)

        if options['print-asm']:
            print(compiled_code)
            return True

        if options['asm']:
            outv = options['asm']
            f = open(outv, 'w')
            w = lang.gbs_vm_serializer.dump(compiled_code, f, style=style(options))
            f.close()
            return True

        runnable = make_runnable(compiled_code, **options)

    except common.utils.SourceException as exception:
        report_program_error(exception.error_type(), exception.msg, exception.area)
        return False # error

    return run_runnable(runnable, **options)

def run_runnable(runnable, **options):
    try:
        board = lang.gbs_board.Board((1, 1))
        if options['from']:
            inb = options['from']
            if not os.path.exists(inb):
                report_error(i18n.i18n('Error'), i18n.i18n('File %s does not exist') % (inb,))
                return False
            fmt = options['from'].split('.')[-1]
            fmt = fmt.lower()
            if fmt not in lang.board.formats.AvailableFormats:
                fmt = lang.board.formats.DefaultFormat
            f = open(inb, 'r')
            board.load(f, fmt=fmt)
            f.close()
        else:
            if options['size']:
                board.clone_from(lang.gbs_board.Board(options['size']))
                board.randomize_contents()
            else:
                board.randomize_full()

        initial_board = board.clone()
        result = runnable.run(board)

        if options['to']:
            f = open(options['to'], 'w') 
            fmt = options['to'].split('.')[-1]
            fmt = fmt.lower()
            if fmt not in lang.board.formats.AvailableFormats:
                fmt = lang.board.formats.DefaultFormat
            board.dump(f, fmt=fmt, style=style(options))
            f.close()

        if options['print-input']:
            print(initial_board)
        if options['print-board']:
            print(board)
        if options['print-retvals']:
            for var, val in result:
                print('%s -> %s' % (var, val))
            if not options['print-board']:
                print('OK')

    except common.utils.SourceException as exception:
        report_program_error(exception.error_type(), exception.msg, exception.area)

    return True

def usage(ret=1):
    msg = i18n.i18n('I18N_gbs_usage') 
    msg = msg.replace('<PROG>', sys.argv[0])
    sys.stderr.write(msg)
    sys.exit(ret)

Option_switches = [
    '--from X',
    '--to X',
    '--size X X',
    '--print-input',
    '--no-print-board',
    '--no-print-retvals',
    '--print-ast',
    '--print-asm',
    '--pprint',
    '--no-typecheck',
    '--no-liveness',
    '--lint X',
    '--asm X',
    '--jit',
    '--print-jit',
    '--print-native',
    '--style X',
    '--version',
    '--license',
    '--help',
]

def maybe(opts, o, else_=None):
    if opts[o] == []:
        return else_
    else:
        return opts[o][0]

def main():

    options = common.utils.parse_options(Option_switches, sys.argv)
    if not options:
        usage()
    arguments, opt = options

    if opt['version']:
        print(common.utils.version_number())
        sys.exit(0)
    elif opt['help']:
        usage(0)
    elif opt['license']:
        print(common.utils.read_file(common.LicenseFile))
        sys.exit(0)

    if opt['size']:
        width, height = opt['size']
        if not common.utils.is_int(width) or not common.utils.is_int(height):
            usage()
        width = int(width)
        height = int(height)
        if width < 1 or height < 1:
            usage()
        opt['size'] = (width, height)
    else:
        opt['size'] = None

    if len(arguments) not in [1, 2]:
        usage()

    opt['from'] = maybe(opt, 'from')
    opt['to'] = maybe(opt, 'to')
    opt['asm'] = maybe(opt, 'asm')

    if len(arguments) == 2:
        if opt['from']:
            usage()
        else:
            opt['from'] = arguments[1]

    opt['lint'] = maybe(opt, 'lint', 'strict')
    if opt['lint'] not in ['lax', 'strict']: usage()

    run_filename(arguments[0], **opt)

if __name__ == '__main__':
    main()

