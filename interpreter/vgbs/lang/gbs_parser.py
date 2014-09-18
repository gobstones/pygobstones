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

import common.position
import lang.bnf_parser
import lang.ast
import lang.gbs_builtins
import common.i18n as i18n
from common.utils import *
import lang.grammar.i18n

#### Parser of Gobstones programs.
####
#### Complements gbs_grammar.bnf solving conflicts and
#### checking for errors.

class GbsParserException(lang.bnf_parser.ParserException):
    pass

TOKEN_BUFFER_SIZE = 4

class GbsLexer(lang.bnf_parser.Lexer):
    """Lexical analyzer that identifies common lexical errors in Gobstones
       source files and solves the conflictive situation in the LL(1) grammar
       by inserting an extra semicolon (;) in the appropiate case."""

    def __init__(self, tokens, reserved, *args, **kwargs):
        lang.bnf_parser.Lexer.__init__(self, tokens, reserved, *args, **kwargs)
        self.reserved_lower = {}
        for x in reserved:
            self.reserved_lower[x.lower()] = x
        for x in lang.gbs_builtins.CORRECT_NAMES:
            self.reserved_lower[x.lower()] = x

    def _tokenize_solve_conflict(self, string, filename):
        self.supertok = lang.bnf_parser.Lexer.tokenize(self, string, filename)
        self.token_queue = []
        q = []
        try:
            self.token_mem = [self._read()]
            yield self.token_mem[0]
            while True:
                curr_tok = self._read()
                self.token_mem.append(curr_tok)
                if self._conflictive_case():
                    # scan input, balancing parentheses
                    op = 1
                    q = [curr_tok]
                    while op > 0:
                        tok = self._read()
                        q.append(tok)
                        if tok.type == '(':
                            op += 1
                        elif tok.type == ')':
                            op -= 1
                    tok = self._read()
                    q.append(tok)
                    if tok.type == ':=': # insert a semicolon
                        yield lang.bnf_parser.Token(';', ';', curr_tok.pos_begin, curr_tok.pos_end)
                    self.token_queue = q + self.token_queue
                    q = []
                else:
                    yield curr_tok
                if len(self.token_mem) > TOKEN_BUFFER_SIZE:
                    self.token_mem.pop(0)
        except StopIteration:
            for tok in q: yield tok

    def _read(self):
        if self.token_queue == []:
            return next(self.supertok)
        else:
            return self.token_queue.pop(0)

    def _conflictive_case(self):
        return len(self.token_mem) >= 3 and \
                      self.token_mem[-3].type == ':=' and \
                      self.token_mem[-2].type == 'lowerid' and \
                      self.token_mem[-1].type == '('

    def tokenize(self, string, filename='...'):
        supertok = self._tokenize_solve_conflict(string, filename)
        previous_token = next(supertok)
        yield previous_token
        open_parens = []
        for tok in supertok:
            area = common.position.ProgramAreaNear(tok)
            if tok.type in ['upperid', 'lowerid']:
                self.warn_if_similar_to_reserved(tok.value, area)

            if tok.type == 'ERROR':
                msg = i18n.i18n('Malformed input - unrecognized symbol')
                raise GbsParserException(msg, common.position.ProgramAreaNear(tok))
            elif tok.type == 'string_start':
                msg = i18n.i18n('Unterminated string')
                raise GbsParserException(msg, common.position.ProgramAreaNear(tok))

            if previous_token.type in ['procedure'] and tok.type not in ['upperid']:
                l1 = i18n.i18n('Found: %s') % tok
                l2 = i18n.i18n('procedure name should be an uppercase identifier')
                raise GbsParserException('\n'.join([l1, l2]), area)
            elif previous_token.type in ['function'] and tok.type not in ['lowerid']:
                l1 = i18n.i18n('Found: %s') % tok
                l2 = i18n.i18n('function name should be a lowercase identifier')
                raise GbsParserException('\n'.join([l1, l2]), area)
            elif tok.type in [',', ';', 'not', 'num', 'string'] and previous_token.type == tok.type:
                raise GbsParserException(i18n.i18n('Repeated symbol: %s') % (tok,), area)
            elif (previous_token.type, tok.type) in [(',', ')'),
                                                     (';', ')'),
                                                     ('(', ','),
                                                    ]:
                msg = i18n.i18n('%s cannot be followed by %s') % (previous_token, tok,)
                raise GbsParserException(msg, area)
            elif previous_token.type == 'return' and tok.type != '(':
                raise GbsParserException(i18n.i18n('return must be followed by "("'), area)
            elif len(self.token_mem) >= 3 and self.token_mem[-3].type == 'THROW_ERROR' and self.token_mem[-1].type != 'string':
                raise GbsParserException(i18n.i18n('THROW_ERROR can only accept a string'), area)

            # check opening/closing parens and braces
            if tok.type in ['(', '{']:
                open_parens.append(tok)
            elif tok.type in [')', '}']:
                # check if there is an opening token
                if len(open_parens) == 0:
                    if tok.type == ')':
                        msg = 'Found closing ")" with no matching open paren'
                    else:
                        msg = 'Found closing "}" with no matching open brace'
                    raise GbsParserException(i18n.i18n(msg), area)
                # check if the opening token is of the right kind
                opening = open_parens.pop()
                if opening.type == '(' and tok.type != ')':
                    open_area = common.position.ProgramAreaNear(opening)
                    l1 = i18n.i18n('Found open "(" with no matching closing paren')
                    l2 = i18n.i18n('Maybe there is an extra "%s" at %s') % (
								tok.type, tok.pos_begin.row_col(),)
                    raise GbsParserException(i18n.i18n('\n'.join([l1, l2])), open_area)
                elif opening.type == '{' and tok.type != '}':
                    open_area = common.position.ProgramAreaNear(opening)
                    l1 = i18n.i18n('Found open "{" with no matching closing brace')
                    l2 = i18n.i18n('Maybe there is an extra "%s" at %s') % (
										tok.type, tok.pos_begin.row_col(),)
                    raise GbsParserException(i18n.i18n('\n'.join([l1, l2])), open_area)

            # check there are no open parens at EOF
            if tok.type == 'EOF' and len(open_parens) > 0:
                opening = open_parens[-1]
                open_area = common.position.ProgramAreaNear(opening)
                if opening.type == '(':
                    msg = i18n.i18n('Found end of file but there are open parens yet')
                    raise GbsParserException(i18n.i18n(msg), open_area)
                elif opening.type == '{':
                    msg = i18n.i18n('Found end of file but there are open braces yet')
                    raise GbsParserException(i18n.i18n(msg), open_area)

            yield tok
            previous_token = tok

    def warn_if_similar_to_reserved(self, value, area):
        tl = value.lower() 
        if tl in self.reserved_lower and self.reserved_lower[tl] != value:
            raise GbsParserException(i18n.i18n('Found: %s\nMaybe should be: %s') % (
                                value, self.reserved_lower[tl]), area)

class GbsParser(lang.bnf_parser.Parser):
    "Parser that identifies common parsing errors in Gobstones source files."

    def __init__(self, syntax, *args, **kwargs):
        lang.bnf_parser.Parser.__init__(self, syntax, *args, **kwargs)

    def parse_error(self, nonterminal, previous_token, token):
        "Raises a GbstonesParserException describing a parse error."
        area = common.position.ProgramAreaNear(token)
        if previous_token.type == 'lowerid' and token.type == '(':
            raise GbsParserException(i18n.i18n('Cannot call a function here'), area)
        elif previous_token.type == 'upperid' and token.type == '(':
            raise GbsParserException(i18n.i18n('Cannot call a procedure here'), area)
        elif previous_token.type == 'upperid' and token.type != '(':
            msg = i18n.i18n('Procedure name "%s" is missing a "("') % (previous_token.value,)
            raise GbsParserException(msg, area)
        elif token.type == 'string':
            l1 = i18n.i18n('Found: %s') % token
            l2 = i18n.i18n('Strings can only be used in a THROW_ERROR command')
            raise GbsParserException('\n'.join([l1, l2]), area)
        elif token.type == 'EOF':
            raise GbsParserException(i18n.i18n('Premature end of input'), area)
        lang.bnf_parser.Parser.parse_error(self, nonterminal, previous_token, token)

class GbsAnalyzer(lang.bnf_parser.Analyzer):
    def __init__(self, grammar, warn=std_warn):
        lang.bnf_parser.Analyzer.__init__(self, GbsLexer, GbsParser, bnf_contents=grammar, warn=warn)

bnf = lang.grammar.i18n.translate(read_file(lang.GbsGrammarFile))
Analyzer = GbsAnalyzer(bnf)

def check_grammar_conflicts():
    """Checks if the BNF grammar has any conflict (an LL(1) prediction
       with two productions)."""
    Analyzer.parser.check_conflicts()

def parse_string(string, filename='...', toplevel_filename=None):
    "Parse a string and return an abstract syntax tree."
    parsing_stream = Analyzer.parse(string, filename)
    start_pos = common.position.Position(string, filename)
    tree = lang.ast.ASTBuilder(start_pos).build_ast_from(parsing_stream)
    tree.source_filename = filename
    if toplevel_filename is None:
        tree.toplevel_filename = tree.source_filename
    else:
        tree.toplevel_filename = toplevel_filename
    return tree

def prelude_for_file(filename):
    prelude_basename = i18n.i18n('Prelude') + '.gbs'
    prelude_filename = os.path.join(os.path.dirname(filename), prelude_basename)
    if os.path.exists(prelude_filename) and os.path.basename(filename) != prelude_basename:
        return prelude_filename
    else:
        return None

def parse_string_try_prelude(string, filename, toplevel_filename=None):
    main_program = parse_string(string, filename, toplevel_filename)

    prelude_filename = prelude_for_file(filename)
    if prelude_filename is not None:
        prelude_barename = i18n.i18n('Prelude')
        pos = common.position.Position(string, filename)
        main_imports = main_program.children[1].children
        main_imports.insert(0, lang.ast.ASTNode([
            'import',
            lang.bnf_parser.Token('upperid', prelude_barename, pos, pos),
            lang.ast.ASTNode([
                lang.bnf_parser.Token('lowerid', '<all>', pos, pos),
            ], pos, pos)
        ], pos, pos))

    return main_program

def parse_file(filename):
    "Parse a file and return an abstract syntax tree."
    return parse_string_try_prelude(read_file(filename), filename)

def token_stream(string):
    return Analyzer.lexer.pure_tokenize(string)

