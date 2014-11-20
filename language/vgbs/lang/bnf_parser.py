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

"""Tokenizer and parser for LL(1) grammars.
The grammar is read in BNF format from a text file.
"""

import re

import common.position
import common.i18n as i18n

BNF_COMMENT_SEQ = "##"
BNF_ESCAPE_SEQ = "$$"

import common.utils
from common.utils import (
    set_new, set_add_change, set_add, seq_sorted
)

class ParserException(common.utils.StaticException):
    "Base exception for syntax errors."

    def error_type(self):
        "Return the error type of these exceptions."
        return i18n.i18n('Syntax error')

def is_nonterminal(string):
    """Returns true if the string represents a nonterminal,
    which must be of the form <...>"""
    return len(string) > 2 and string[0] == '<' and string[-1] == '>'

class Token(common.position.ProgramElement):
    "Represents a token (terminal symbol in the grammar)."

    def __init__(self, type_, value, pos_begin, pos_end):
        common.position.ProgramElement.__init__(self)
        self.type = type_
        self.value = value
        self.pos_begin = pos_begin
        self.pos_end = pos_end

    def type_description(cls, tok_type):
        """Return the human-readable description of a token type,
        for displaying errors."""
        return i18n.Token_type_descriptions.get(tok_type, '"' + tok_type + '"')
    type_description = classmethod(type_description)

    def __repr__(self):
        if self.type in ['EOF', 'BOF']:
            return Token.type_description(self.type)
        else:
            if len(self.value) > 0 and self.value[0] == '"':
                quoted = self.value
            else:
                quoted = '"' + self.value + '"'
            if self.type in i18n.Token_type_descriptions:
                return '%s %s' % (Token.type_description(self.type), quoted)
            else:
                return '%s' % (quoted,)

    def description(self):
        """Return the human-readable description of a token."""
        return repr(self)

    def has_children(self):
        """A token has no children."""
        return False

    def show_ast(self, indent=0, **_):
        """Display the Token as a leaf AST."""
        return '    ' * indent + self.value

    def negate(self):
        """Negate a token (should represent a numeric value)."""
        assert self.type == 'num'
        return Token(self.type, '-' + self.value, self.pos_begin, self.pos_end)

def fake_bof():
    """Return a dummy token. Useful for reporting errors that
    do not occur in a clear point of the program."""
    pos = common.position.Position('', '')
    return common.position.ProgramAreaNear(Token('BOF', 'BOF', pos, pos))

class Lexer(object):
    "Lexical analyzer."

    def __init__(self, tokens, reserved, warn=common.utils.std_warn):
        self.tokens = tokens
        self.reserved = reserved
        self.warn = warn

    def pure_tokenize(self, string, filename='...'):
        "Generates a stream of tokens for the given string."
        pos = common.position.Position(string, filename)
        previous_token = Token('BOF', 'BOF', pos, pos)
        yield previous_token
        while pos.start < len(string):
            for tok_type, tok_regexp in self.tokens:
                match = tok_regexp.match(string, pos.start)
                if not match:
                    continue
                tok_val = string[match.start():match.end()]
                next_pos = pos.after_reading(tok_val)
                previous_token = Token(tok_type, tok_val, pos, next_pos)
                yield previous_token
                pos = next_pos
                break
            else:
                symb = string[pos.start]
                next_pos = pos.after_reading(symb)
                yield Token('ERROR', symb, pos, next_pos)
                pos = next_pos
        yield Token('EOF', 'EOF', pos, pos)

    def tokenize(self, string, filename='...'):
        """Generates a stream of tokens for the given string,
        ignoring whitespace and comments, and recognizing reserved
        words and operators."""
        for tok in self.pure_tokenize(string, filename):
            if tok.type == 'WHITESPACE' or tok.type == 'COMMENT':
                continue
            if tok.value in self.reserved:
                yield Token(tok.value, tok.value, tok.pos_begin, tok.pos_end)
            else:
                yield tok

class Production(object):
    "Represents a production with rule and possibly an associated action."

    def __init__(self, raw_bnf_rule):
        rule_action = raw_bnf_rule.split('@')
        self.rule = tuple(common.utils.trim_blanks(rule_action[0]).split(' '))
        if len(rule_action) == 1:
            self.action = None
        else:
            self.action = common.utils.trim_blanks(rule_action[1]).split(' ')

    def __repr__(self):
        if self.action:
            action = ' @ ' + ' '.join(self.action)
        else:
            action = ''
        return ' '.join(self.rule) + action

def bnf_rule_to_str(rule):
    "Convert a BNF rule to a string."
    return '  ' + '\n| '.join([str(p) for p in rule.values()]) + '\n'

class Parser(object):
    "Parser for LL(1) grammars."

    def __init__(self, syntax, warn=common.utils.std_warn):
        self.syntax = syntax
        self.warn = warn

        self._first = None
        self._build_first()

        self._follow = None
        self._build_follow()

        self._parse_table = None
        self._build_table()

    def all_nonterminals(self):
        "Returns all the nonterminals that have productions in the grammar."
        return self.syntax.keys()

    def _is_nullable(self, symbol):
        "Returns True iff the symbol is currently nullable."
        if symbol == '':
            return True
        return is_nonterminal(symbol) and '' in self._first[symbol]

    def _non_nullable_head(self, symbol):
        "Returns the non-nullable subset of the FIRST set of the given symbol."
        if symbol == '':
            return set_new()
        elif is_nonterminal(symbol):
            return [s for s in self._first[symbol] if s != '']
        else:
            return set_new([symbol])

    def _build_first(self):
        """Builds a table that associates each nonterminal with
        its FIRST set."""
        self._first = {}
        for nonterminal in self.all_nonterminals():
            self._first[nonterminal] = set_new()
        change = True
        while change:
            change = False
            for nonterminal in self.all_nonterminals():
                for production in self.syntax[nonterminal]:
                    if self._build_first_seq(self._first[nonterminal],
                                             production.rule):
                        change = True

    def _build_first_seq(self, first_set, seq):
        """Fill `first_set` with the current FIRST set of the string of
        symbols `seq`. Returns True if `first_set` is changed and False
        otherwise."""
        change = False
        for symbol in seq:
            for fst in self._non_nullable_head(symbol):
                if set_add_change(first_set, fst):
                    change = True
            if not self._is_nullable(symbol):
                break
        else:
            if set_add_change(first_set, ''):
                change = True
        return change

    def first(self, alpha):
        """Returns the FIRST set of a string alpha (FIRST(alpha)).
        A terminal symbol x is in FIRST(alpha) iff alpha =>* x...
        The empty string '' is in FIRST(alpha) iff alpha =>* ''"""
        first_set = set_new()
        self._build_first_seq(first_set, alpha)
        return first_set
  
    def _build_follow(self):
        "Builds a table that associates each nonterminal with its FOLLOW set."
        self._follow = {}
        for nonterminal in self.all_nonterminals():
            self._follow[nonterminal] = set_new()
        self._follow['<start>'] = set_new(['EOF'])
        change = True
        while change:
            change = False
            for nonterminal in self.all_nonterminals():
                for production in self.syntax[nonterminal]:
                    for i in range(len(production.rule)):
                        rule = production.rule[i]
                        if not is_nonterminal(rule):
                            continue
                        beta = production.rule[i + 1:]
                        if self._build_follow_seq(nonterminal,
                                                  self._follow[rule],
                                                  beta):
                            change = True

    def _build_follow_seq(self, nonterminal, follow_set, seq):
        """Fill `follow_set` with the current FOLLOW set of the string of
        symbols `seq`. Returns True if `follow_set` is changed and False
        otherwise."""
        change = False
        first_seq = self.first(seq)
        for symb in first_seq:
            if symb == '':
                continue
            if set_add_change(follow_set, symb):
                change = True
        if '' in first_seq:
            for symb in self.follow(nonterminal):
                if set_add_change(follow_set, symb):
                    change = True
        return change

    def follow(self, nonterm):
        """Returns the FOLLOW set of a given nonterminal A (FOLLOW(A)).
        A terminal symbol x is in FOLLOW(A) iff <start> =>* ...Ax...
        EOF is in FOLLOW(A) iff <start> =>* ...A"""
        return self._follow[nonterm]

    def _fill_table(self, nonterminal, terminal, production): 
        """Adds the given production to the entry (nonterminal, terminal) of
        the parsing table."""
        key = (nonterminal, terminal)
        if key not in self._parse_table:
            self._parse_table[key] = set_new()
        self._parse_table[key][id(production)] = production

    def _build_table(self):
        "Builds the LL(1) parsing table."
        self._parse_table = {}
        for nonterminal in self.all_nonterminals():
            for production in self.syntax[nonterminal]:
                follow = set_new()
                self._build_follow_seq(nonterminal, follow, production.rule)
                for terminal in follow:
                    self._fill_table(nonterminal, terminal, production)

    def _followups(self, nonterm):
        """Return the set of token types that could follow the given
        nonterminal."""
        res = {}
        for nonterm2, symb in self._parse_table.keys():
            if nonterm == nonterm2:
                set_add(res, symb)
        return seq_sorted([Token.type_description(key) for key in res.keys()])

    def check_conflicts(self):
        "Checks the grammar for conflicts."
        for (nonterminal, terminal), productions in self._parse_table.items():
            if len(productions.keys()) != 1:
                self._warn_conflict(nonterminal, terminal, None)

    def parse_error(self, top, _previous_token, token):
        "Raises a ParserException describing a parse error."
        if is_nonterminal(top):
            follow = self._followups(top) 
        else:
            follow = [Token.type_description(top)]
        if len(follow) == 1:
            msg = i18n.i18n('Found: %s\nExpected: %s') % (token, follow[0])
        else:
            msg = ''
            msg += i18n.i18n('\n'.join([
                                'Found: %s',
                                'Expected one of the following tokens:'])) % (
                     token,)
            msg += '\n' + common.utils.indent('\n'.join(follow))
        raise ParserException(msg, common.position.ProgramAreaNear(token))

    def _warn_conflict(self, nonterminal, terminal, area):
        "Emits a warning for a conflictive state."
        msg = ''
        msg += i18n.i18n('Conflictive rule for: ("%s", "%s")\n') % (
                    nonterminal, terminal)
        msg += i18n.i18n('Will choose first production:\n')
        msg += common.utils.indent(bnf_rule_to_str(
                        self._parse_table[(nonterminal, terminal)]))
        self.warn(ParserException(msg, area))

    def parse(self, token_stream):
        "Parse a token stream."
        stack = ['<start>']
        previous_token = next(token_stream) # BOF
        token = next(token_stream)
        while stack != []:
            top = stack[-1]
            if is_nonterminal(top):
                productions = self._parse_table.get((top, token.type), None)
                if productions is not None:
                    #if len(productions) != 1:
                    #  self._warn_conflict(
                    #       top,
                    #       token.type,
                    #       common.position.ProgramAreaNear(token))
                    # in case of conflict, choose the lexically least production
                    production = common.utils.dict_min_value(
                                    productions,
                                    key=lambda p: p.rule)
                    stack.pop()

                    res_nonterm = None
                    for nonterm in common.utils.seq_reversed(production.rule):
                        if nonterm != '':
                            stack.append(nonterm)
                        res_nonterm = nonterm

                    yield 'PRODUCE', res_nonterm, production
                else:
                    self.parse_error(top, previous_token, token)
            else:
                if top == token.type:
                    yield 'CONSUME', top, token
                    previous_token = token
                    token = next(token_stream)
                    stack.pop()
                else:
                    self.parse_error(top, previous_token, token)

def remove_comment_in_line(line):
    "Remove comment part from line."
    return line.split(BNF_COMMENT_SEQ)[0]

def remove_comments(contents):
    "Remove comments from string."       
    return '\n'.join([
        remove_comment_in_line(line) for line in contents.split('\n')
    ])

def _bnf_escape(contents):
    "Translate strings into the corresponding escape sequences."    
    contents = remove_comments(contents)
    for original, escaped in Analyzer.Escape_sequences:
        contents = contents.replace(original, escaped)
    return contents

def _bnf_unescape(contents):
    "Translate escape sequences into the original strings."
    for original, escaped in Analyzer.Escape_sequences: 
        contents = contents.replace(escaped, original)
    return contents

class Analyzer(object):
    """Represents a syntax analyzer for a given BNF LL(1) grammar.
    anAnalyzer.parse(string) is a generator that yields two kinds of
    parsing events:
        ('CONSUME', terminal_symbol,    token)
        ('PRODUCE', nonterminal_symbol, production)

    Example:

        >>> a = Analyzer(Lexer, Parser, bnf_filename='gbs_grammar.txt')
        >>> for evt in a.parse('procedure Main() {}'):
        ...     print(evt)
        ...
        ('PRODUCE', '<gobstones>', <gobstones>)
        ('PRODUCE', '<defs>', <defs>)
        ('PRODUCE', '<def>', <def> <defs> @ ++ [$1] $2)
        ('PRODUCE', 'procedure', procedure <procName> <params> <procFuncBody> @ procedure $2 $3 $4)
        ('CONSUME', 'procedure', "procedure")
        ...
    """

    def __init__(self, lexer_class, parser_class, **kwargs):
        # Recognized kwargs:
        #
        #   bnf_contents: raw string
        #   bnf_filename: filename
        #   warn: warning function

        self.lexer_class = lexer_class
        self.parser_class = parser_class
        self.warn = kwargs.get('warn', common.utils.std_warn)

        self.lexer = None
        self.parser = None

        assert ('bnf_contents' in kwargs) != ('bnf_filename' in kwargs)
        if 'bnf_contents' in kwargs:
            self._read_bnf(kwargs['bnf_contents'])
        else:
            self._read_bnf_from_file(kwargs['bnf_filename'])

    def _read_bnf_from_file(self, filename):
        "Build the parser reading the BNF grammar from the given file."
        self._read_bnf(common.utils.read_file(filename))

    def _read_bnf(self, bnf_contents):
        "Builds the parser reading the BNF grammar from the given string."
        tokens = []
        reserved = []
        syntax = {}
        raw_bnf = _bnf_escape(bnf_contents)
        all_productions = [
            common.utils.trim(prod)
            for prod in raw_bnf.split(';;')
            if common.utils.nonempty(common.utils.trim(prod))
        ]
        for production in all_productions:
            head, rules = [
                common.utils.trim(part)
                for part in production.split('::=')
            ]
            rules = [
                _bnf_unescape(common.utils.trim(part))
                for part in rules.split('|')
            ]
            if head == 'RESERVED':
                reserved.extend(rules)
            elif is_nonterminal(head):
                syntax[head] = [Production(prod) for prod in rules]
            else:
                tokens.append((head, re.compile('|'.join(rules))))

        self.lexer = self.lexer_class(tokens, reserved, self.warn)
        self.parser = self.parser_class(syntax, self.warn)

    Escape_sequences = [
        ("||", BNF_ESCAPE_SEQ + "(OR)"),
        ("#", BNF_ESCAPE_SEQ + "(PYCOMMENT)")
    ]

    def parse(self, string, filename='...'):
        """Parse the given string. The filename is used for informational
        purposes only (the file is not read)."""
        token_stream = self.lexer.tokenize(string, filename)
        return self.parser.parse(token_stream)

