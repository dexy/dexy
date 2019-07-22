from dexy.exceptions import UserFeedback, InternalDexyProblem
from dexy.filters.pyg import PygmentsFilter
from pygments import highlight
import ply.lex as lex
import ply.yacc as yacc

class LexError(InternalDexyProblem):
    pass

class ParseError(UserFeedback):
    pass

tokens = (
    'AMP',
    'AT',
    'CODE',
    'COLONS',
    'DBLQUOTE',
    'END',
    'IDIOCLOSE',
    'IDIOOPEN',
    'EXP',
    'IDIO',
    'NEWLINE',
    'SGLQUOTE',
    'WHITESPACE',
    'WORD',
)

states = (
    ('idiostart', 'exclusive',),
    ('idio', 'exclusive',),
)

class Id(PygmentsFilter):
    """
    Splits files into sections based on comments like ### "foo"

    Replacement for idiopidae. Should be fully backwards-compatible.

    For more information about the settings starting with ply-, see the PLY
    YACC parser documentation http://www.dabeaz.com/ply/ply.html#ply_nn36
    """
    aliases = ['idio', 'id', 'idiopidae', 'htmlsections']
    _settings = {
            'examples' : ['idio', 'htmlsections'],
            'highlight' : ("Whether to apply syntax highlighting to sectional output.", None),
            'skip-extensions' : ("Because |idio gets applied to *.*, need to make it easy to skip non-textual files.", (".odt")),
            'remove-leading' : ("If a document starts with empty section named '1', remove it.", False),
            'ply-optimize' : ("Whether to use optimized mode for the lexer.", 1),
            'ply-write-tables' : ("Whether to generate parser table files (which will be stored in ply-outputdir and named ply-tabmodule).", 1),
            'ply-outputdir' : ("Location relative to where you run dexy in which ply will store table files. Defaults to dexy's log directory.", None),
            'ply-parsetab' : ("Name of parser tabfile (.py extension will be added) to be stored in ply-outputdir if ply-write-tables set to 1.", 'id_parsetab'),
            'ply-lextab' : ("Name of lexer tabfile (.py extension will be added) to be stored in ply-outputdir if ply-optimize is set to 1.", 'id_lextab'),
            'output-extensions' : PygmentsFilter.MARKUP_OUTPUT_EXTENSIONS + PygmentsFilter.IMAGE_OUTPUT_EXTENSIONS
            }

    def process(self):
        try:
            input_text = str(self.input_data)
        except UnicodeDecodeError:
            self.output_data['1'] = "non textual"
            self.output_data.save()
            return

        lexer.outputdir = self.setting('ply-outputdir')
        lexer.errorlog = self.doc.wrapper.log
        lexer.remove_leading = self.setting('remove-leading')
        parser.outputdir = self.setting('ply-outputdir')
        parser.errorlog = self.doc.wrapper.log
        parser.write_tables = self.setting('ply-write-tables')

        _lexer = lexer.clone()
        _lexer.sections = []
        _lexer.level = 0
        start_new_section(_lexer, 0, 0, _lexer.level)

        parser.parse(input_text + "\n", lexer=_lexer)
        strip_trailing_newline(_lexer)
        parser_output = _lexer.sections

        pyg_lexer = self.create_lexer_instance()
        pyg_formatter = self.create_formatter_instance()

        # TODO fix file extension if highlight is set to false
        do_highlight = self.setting('highlight')
        if do_highlight is None:
            if self.alias in ('htmlsections',):
                do_highlight = False
                if self.output_data.setting('canonical-output') is None:
                    self.output_data.update_settings({'canonical-output' : True})
            else:
                do_highlight = True

        for section in parser_output:
            if do_highlight:
                section['contents'] = highlight(section['contents'], pyg_lexer, pyg_formatter)
            self.output_data._data.append(section)
        self.output_data.save()

def t_error(t):
    raise LexError("Problem lexing at position %s." % t.lexpos)

def t_idio_error(t):
    print("comment '%s'" % t.lexer.lexdata[t.lexer.comment_start_pos:])
    print("all '%s'" % t.lexer.lexdata)
    print("char '%s'" % t.lexer.lexdata[t.lexpos-1:t.lexer.lexpos])
    raise LexError("Problem lexing in 'idio' state at position %s." % t.lexpos)

def t_idiostart_error(t):
    raise LexError("Problem lexing in 'idiostart' state at position %s." % t.lexpos)
        
def append_text(lexer, code):
    """
    Append to the currently active section.
    """
    set_current_section_contents(lexer, current_section_contents(lexer) + code)

def current_section_exists(lexer):
    return len(lexer.sections) > 0

def current_section_empty(lexer):
    return len(current_section_contents(lexer)) == 0

def current_section_contents(lexer):
    return lexer.sections[-1]['contents']

def set_current_section_contents(lexer, text):
    lexer.sections[-1]['contents'] = text

def strip_trailing_newline(lexer):
    set_current_section_contents(lexer, current_section_contents(lexer).rsplit("\n",1)[0])

def start_new_section(lexer, position, lineno, new_level, name=None):
    if name:
        if lexer.remove_leading:
            if len(lexer.sections) == 1 and current_section_empty(lexer):
                lexer.sections = []
    else:
        # Generate anonymous section name.
        name = str(len(lexer.sections)+1)

    try:
        change_level(lexer, new_level)
    except Exception:
        print(name)
        raise

    lexer.sections.append({
            'name' : name.rstrip(),
            'position' : position,
            'lineno' : lineno,
            'contents' : '',
            'level' : lexer.level
            })

def change_level(lexer, new_level):
    if new_level == lexer.level:
        pass
    elif new_level < lexer.level:
        pass
    elif new_level == lexer.level + 1:
        pass
    elif new_level > (lexer.level + 1):
        msg = "attempting to indent more than 1 level to %s from previous level %s"
        msgargs = (new_level, lexer.level)
        raise Exception(msg % msgargs)
    elif new_level < 0:
        raise Exception("attepmting to indent to level below 0, does not exist")
    else:
        msg = "logic error! new level %s current level %s"
        msgargs = (new_level, lexer.level)
        raise Exception(msg % msgargs)

    lexer.level = new_level

def next_char(t):
    return t.lexer.lexdata[t.lexer.lexpos:t.lexer.lexpos+1]

def lookahead_n(t, n):
    # TODO what if n is too big?
    return t.lexer.lexdata[t.lexer.lexpos:t.lexer.lexpos+n]

def lookahead_for(t, word):
    return lookahead_n(t, len(word)) == word

def lookahead_for_any(t, words):
    any_found = False
    for word in words:
        if lookahead_for(t, word):
            any_found = True
            break
    return any_found

# Lexer tokens for idio state
def t_idio_AT(t):
    r'@'
    return t

def t_idio_AMP(t):
    r'&'
    return t

def t_idio_COLONS(t):
    r':+'
    return t

def t_idio_DBLQUOTE(t):
    r'"'
    return t

def t_idio_SGLQUOTE(t):
    r'\''
    return t

def t_idio_EXP(t):
    r'export|section'
    return t

def t_idio_END(t):
    r'end'
    return t

def t_idio_WHITESPACE(t):
    r'(\ |\t)+'
    return t

def t_idio_NEWLINE(t):
    r'\r\n|\n|\r'
    exit_idio_state(t)
    return t

def t_idio_IDIOCLOSE(t):
    r'(-->)|(\*/)'
    if not t.lexer.idio_expect_closing_block:
        raise UserFeedback("Unexpected code %s in an idio block" % t.value)
    return t

def t_idio_WORD(t):
    r'[0-9a-zA-Z-_]+'
    return t

def t_idio_OTHER(t):
    r'.'
    t.type = 'CODE'
    exit_idio_state(t)
    return t

def exit_idio_state(t):
    if not t.lexer.idio_expect_closing_block:
        t.lexer.pop_state()
    t.lexer.pop_state()

# Lexer tokens and helpers for idiostart state
def idiostart_incr_comment(t):
    if t.lexer.comment_char == t.value:
        t.lexer.comment_char_count += 1
    else:
        return idiostart_abort(t)

def idiostart_abort(t):
    t.value = t.lexer.lexdata[t.lexer.comment_start_pos:t.lexer.lexpos]
    t.type = "CODE"
    t.lexer.pop_state()
    return t

def t_idiostart_COMMENT(t):
    r'\#|%|;|/|C|!'
    return idiostart_incr_comment(t)

def t_idiostart_SPACE(t):
    r'\ +'
    if t.lexer.comment_char_count != 3:
        return idiostart_abort(t)
    else:   
        t.lexer.push_state('idio')
        t.value = t.lexer.lexdata[t.lexer.comment_start_pos:t.lexer.lexpos]
        t.type = 'IDIO'
        return t

def t_idiostart_ABORT(t):
    r'[^#;/% ]'
    return idiostart_abort(t)

# Lexer tokens and helpers for initial state
def start_idiostart(t):
    if next_char(t) == '\n':
        t.type = 'CODE'
        return t
    else:
        t.lexer.comment_char = t.value
        t.lexer.comment_char_count = 1
        t.lexer.comment_start_pos = t.lexer.lexpos - 1
        t.lexer.idio_expect_closing_block = False
        t.lexer.push_state('idiostart')

def t_IDIOOPEN(t):
    r'(<!--|/\*\*\*)\ +@?'
    if lookahead_for_any(t, ['export', 'section', 'end']):
        t.lexer.push_state('idio')
        t.lexer.idio_expect_closing_block = True
        return t
    else:
        t.type = 'CODE'
        return t

def t_COMMENT(t):
    r'\#|%|;|/|C|!'
    return start_idiostart(t)

def t_NEWLINE(t):
    r'\r\n|\n|\r'
    return t

def t_WHITESPACE(t):
    r'[\ \t]+'
    return t

def t_CODE(t):
    r'[^\#/\n\r]+'
    return t

def p_main(p):
    '''entries : entries entry
               | entry'''
    pass

def p_entry(p):
    '''entry : NEWLINE
             | falsestart
             | codes NEWLINE
             | codes inlineidio NEWLINE
             | idioline NEWLINE'''
    p.lexer.lineno += 1
    if len(p) == 2:
        append_text(p.lexer, p[1])
    elif len(p) == 3:
        if p[1]:
            append_text(p.lexer, p[1] + '\n')
        pass
    elif len(p) == 4:
        code_content = p[1]
        append_text(p.lexer, code_content + "\n")
        # TODO Process inlineidio directives @elide &tag
        # inlineidio_content = p[2]
    else:
        raise Exception("unexpected length " + len(p))

def p_sectionfalsestart(p):
    '''falsestart : IDIO words NEWLINE
                  | IDIO words IDIO NEWLINE
                  | IDIO quote words quote NEWLINE
                  | codes IDIO anythings NEWLINE
                  | WHITESPACE IDIO anythings IDIO NEWLINE
                  | WHITESPACE IDIO anythings NEWLINE'''
    p[0] = "".join(p[1:])

def p_anythings(p):
    '''anythings : anythings anything
                 | anything'''
    p[0] = ''.join(p[1:len(p)])

def p_anything(p):
    '''anything : WORD
                | WHITESPACE
                | CODE'''
    p[0] = p[1]

def p_codes(p):
    '''codes : codes codon
             | codon'''
    if len(p) == 2:
        p[0] = p[1]
    elif len(p) == 3:
        if p[1]:
            p[0] = p[1] + p[2]
        else:
            p[0] = p[2]

def p_codon(p):
    '''codon : CODE 
             | WHITESPACE'''
    p[0] = p[1]

def p_inlineidio(p):
    '''inlineidio : IDIO AMP WORD'''
    p[0] = p[1] + p[2] + p[3]

def p_idioline(p):
    '''idioline : idio
                | idio WHITESPACE
                | WHITESPACE idio
                | WHITESPACE idio WHITESPACE'''
    pass

def p_linecontent(p):
    '''idio : export
            | exportq
            | exportql
            | sectionstart
            | closedcomment
            | closedcommentlevels
            | closedcommentq
            | closedcommentql
            | end '''
    pass

## Methods Defining Section Boundaries
def p_sectionstart(p):
    '''sectionstart : IDIO quote WORD quote
                    | IDIO quote COLONS WORD quote'''
    if len(p) == 5:
        # no colons, so level is 0
        start_new_section(p.lexer, p.lexpos(1), p.lineno(1), 0, p[3])
    elif len(p) == 6:
        start_new_section(p.lexer, p.lexpos(1), p.lineno(1), len(p[3]), p[4])
    else:
        raise Exception("unexpected length %s" % len(p))

def p_closed_comment(p):
    '''closedcomment : IDIOOPEN EXP WHITESPACE WORD IDIOCLOSE
                     | IDIOOPEN EXP WHITESPACE WORD WHITESPACE IDIOCLOSE'''
    assert len(p) in [6,7]
    start_new_section(p.lexer, p.lexpos(1), p.lineno(1), 0, p[4])

def p_closed_comment_levels(p):
    '''closedcommentlevels : IDIOOPEN EXP WHITESPACE COLONS WORD IDIOCLOSE
                           | IDIOOPEN EXP WHITESPACE COLONS WORD WHITESPACE IDIOCLOSE'''
    assert len(p) in [7,8]
    start_new_section(p.lexer, p.lexpos(1), p.lineno(1), len(p[4]), p[5])

def p_closed_comment_quoted(p):
    '''closedcommentq : IDIOOPEN EXP WHITESPACE quote words quote IDIOCLOSE
                      | IDIOOPEN EXP WHITESPACE quote words quote WHITESPACE IDIOCLOSE'''
    assert len(p) in [8,9]
    start_new_section(p.lexer, p.lexpos(1), p.lineno(1), 0, p[5])

def p_closed_comment_quoted_with_language(p):
    '''closedcommentql : IDIOOPEN EXP WHITESPACE quote words quote WHITESPACE WORD IDIOCLOSE
                       | IDIOOPEN EXP WHITESPACE quote words quote WHITESPACE WORD WHITESPACE IDIOCLOSE'''
    assert len(p) in [10,11]
    start_new_section(p.lexer, p.lexpos(1), p.lineno(1), 0, p[5])

## Old Idiopidae @export syntax
def p_export(p):
    '''export : IDIO AT EXP WHITESPACE words
              | IDIO AT EXP WHITESPACE words WHITESPACE'''
    assert len(p) in [6,7]
    start_new_section(p.lexer, p.lexpos(1), p.lineno(1), 0, p[5])

def p_export_quoted(p):
    '''exportq : IDIO AT EXP WHITESPACE quote words quote
               | IDIO AT EXP WHITESPACE quote words quote WHITESPACE'''
    assert len(p) in [8,9]
    start_new_section(p.lexer, p.lexpos(1), p.lineno(1), 0, p[6])

def p_export_quoted_with_language(p):
    '''exportql : IDIO AT EXP WHITESPACE quote words quote WHITESPACE words
                | IDIO AT EXP WHITESPACE quote words quote WHITESPACE words WHITESPACE'''
    assert len(p) in [10,11]
    start_new_section(p.lexer, p.lexpos(1), p.lineno(1), 0, p[6])

def p_end(p):
    '''end : IDIO AT END
           | IDIOOPEN END IDIOCLOSE
           | IDIOOPEN END WHITESPACE IDIOCLOSE
           | IDIOOPEN EXP WHITESPACE quote END quote WHITESPACE IDIOCLOSE'''
    start_new_section(p.lexer, p.lexpos(1), p.lineno(1), p.lexer.level)

def p_quote(p):
    '''quote : DBLQUOTE
             | SGLQUOTE'''
    p[0] = p[1]

def p_words(p):
    '''words : words WHITESPACE WORD
             | WORD'''
    if len(p) == 4:
        p[0] = p[1] + p[2] + p[3]
    elif len(p) == 2:
        p[0] = p[1]
    else:
        raise Exception("unexpected length %s" % len(p))

def p_error(p):
    if not p:
        raise ParseError("Reached EOF when parsing file using idioipdae.")

    lines = p.lexer.lexdata.splitlines()
    this_line = lines[p.lineno-1]

    # Add whole line.
    append_text(p.lexer, this_line+"\n")

    # Forward input to end of line
    while 1:
        tok = yacc.token()
        if not tok or tok.type == 'NEWLINE': break

    yacc.restart()

def tokenize(text, lexer):
    """
    Return array of lexed tokens (for debugging).
    """
    lexer.input(text)
    tokens = []
    while True:
        tok = lexer.token()
        if not tok: break      # No more input
        tokens.append(tok)
    return tokens

def token_info(text, lexer):
    """
    Returns debugging information about lexed tokens as a string.
    """
    def tok_info(tok):
        return "%03d %-15s %s" % (tok.lexpos, tok.type, tok.value.replace("\n",""))
    return "\n".join(tok_info(tok) for tok in tokenize(text, lexer))

# This is outside of the wrapper system so we aren't aware of user-specified
# artifacts directory. Just use .dexy if it's there and don't write files if not.

import os
if os.path.exists(".dexy"):
    outputdir=".dexy"
    lexer = lex.lex(optimize=1, lextab="id_lextab", outputdir=outputdir)
    parser = yacc.yacc(tabmodule="id_parsetab",debug=0, outputdir=outputdir)
else:
    lexer = lex.lex(optimize=0)
    parser = yacc.yacc(write_tables=0, debug=0)
