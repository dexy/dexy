from dexy.common import OrderedDict
from dexy.exceptions import UserFeedback
import ply.lex as lex
import ply.yacc as yacc

sections = OrderedDict()
level = 0
remove_leading_empty_anonymous_section = None

def append_text(code):
    """
    Append to the currently active section.
    """
    set_current_section_contents(current_section_contents() + code)

def current_section_exists():
    return len(sections) > 0

def current_section_key():
    return sections.keys()[-1]

def current_section_contents():
    return sections[current_section_key()]['contents']

def current_section_empty():
    return len(current_section_contents()) == 0

def set_current_section_contents(text):
    sections[current_section_key()]['contents'] = text

def clean_completed_section():
    """
    Cleans trailing newline and any whitespace following trailing newline.
    """
    splits = current_section_contents().rsplit("\n",1)
    set_current_section_contents(splits[0])

def start_new_section(position, lineno, new_level, name=None):
    if current_section_exists():
        clean_completed_section()

    if name:
        if remove_leading_empty_anonymous_section:
            if len(sections) == 1 and current_section_empty():
                del sections[u'1']
    else:
        # Generate anonymous section name.
        name = unicode(len(sections)+1)

    try:
        change_level(new_level)
    except Exception as e:
        print name
        raise e

    sections[name.rstrip()] = {
            'position' : position,
            'lineno' : lineno,
            'contents' : u'',
            'level' : level
            }

tokens = (
        'CODE',
        'NEWLINE',

        'IDIO',

        # in idio block
        'AT',
        'AMP',
        'COLONS',
        'DBLQUOTE',
        'SGLQUOTE',
        'EXP',
        'END',
        'WHITESPACE',
        'WORD'
        )

states = (
        ('idiostart', 'exclusive',),
        ('idio', 'exclusive',),
        )

def next_char(t):
    return t.lexer.lexdata[t.lexer.lexpos:t.lexer.lexpos+1]

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
    r'export'
    return t

def t_idio_END(t):
    r'end'
    return t

def t_idio_WHITESPACE(t):
    r'(\ |\t)+'
    return t

def t_idio_NEWLINE(t):
    r'\r\n|\n|\r'
    t.lexer.pop_state()
    t.lexer.pop_state()
    return t

def t_idio_WORD(t):
    r'[a-zA-Z-]+'
    return t

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

def t_idiostart_OCTOTHORPE(t):
    r'\#'
    return idiostart_incr_comment(t)

def t_idiostart_FWDSLASH(t):
    r'/'
    return idiostart_incr_comment(t)

def t_idiostart_SPACE(t):
    r'\ '
    if t.lexer.comment_char_count != 3:
        return idiostart_abort(t)
    else:   
        t.lexer.push_state('idio')
        t.value = t.lexer.lexdata[t.lexer.comment_start_pos:t.lexer.lexpos]
        t.type = 'IDIO'
        return t

def t_idiostart_ABORT(t):
    r'[^#/ ]'
    return idiostart_abort(t)

# INITIAL state tokens

def start_idiostart(t):
    t.lexer.comment_char = t.value
    t.lexer.comment_char_count = 1
    t.lexer.comment_start_pos = t.lexer.lexpos - 1
    t.lexer.push_state('idiostart')

def t_OCTOTHORPE(t):
    r'\#'
    start_idiostart(t)

def t_FWDSLASH(t):
    r'/'
    start_idiostart(t)

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
             | codes NEWLINE
             | codes inlineidio NEWLINE
             | idioline NEWLINE'''
    p.lexer.lineno += 1
    if len(p) == 2:
        append_text('\n')
    elif len(p) == 3:
        if p[1]:
            append_text(p[1] + '\n')
        pass
    elif len(p) == 4:
        code_content = p[1]
        append_text(code_content + "\n")
        # TODO Process inlineidio directives @elide &tag
        # inlineidio_content = p[2]
    else:
        raise Exception("unexpected length " + len(p))

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
            | end '''
    pass

def change_level(new_level):
    global level

    if new_level == level:
        print "remaining at same level"
    elif new_level == level + 1:
        print "indenting 1 level"
    elif new_level > (level + 1):
        print "new level", new_level
        print "current level", level
        raise Exception("attempting to indent more than 1 level from previous level")
    elif new_level < 0:
        raise Exception("attepmting to indent to level below 0, does not exist")
    elif new_level < level:
        print "de-denting to %s" % new_level
    else:
        raise Exception("logic error! new level %s level %s" % (new_level, level))

    level = new_level

## Methods Defining Section Boundaries
def p_sectionstart(p):
    '''sectionstart : IDIO WORD
                    | IDIO COLONS WORD'''
    if len(p) == 3:
        start_new_section(p.lexpos(1), p.lineno(1), 0, p[2])
    elif len(p) == 4:
        start_new_section(p.lexpos(1), p.lineno(1), len(p[2]), p[3])
    else:
        raise Exception("unexpected length %s" % len(p))

## Old Idiopidae @export syntax
def p_export(p):
    '''export : IDIO AT EXP WHITESPACE words
              | IDIO AT EXP WHITESPACE words WHITESPACE'''
    assert len(p) in [6,7]
    start_new_section(p.lexpos(1), p.lineno(1), 0, p[5])

def p_export_quoted(p):
    '''exportq : IDIO AT EXP WHITESPACE quote words quote
               | IDIO AT EXP WHITESPACE quote words quote WHITESPACE'''
    assert len(p) in [8,9]
    start_new_section(p.lexpos(1), p.lineno(1), 0, p[6])

def p_export_quoted_with_language(p):
    '''exportql : IDIO AT EXP WHITESPACE quote words quote WHITESPACE words
                | IDIO AT EXP WHITESPACE quote words quote WHITESPACE words WHITESPACE'''
    assert len(p) in [10,11]
    start_new_section(p.lexpos(1), p.lineno(1), 0, p[6])

def p_end(p):
    '''end : IDIO AT END'''
    start_new_section(p.lexpos(1), p.lineno(1), level)

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
    raise UserFeedback("invalid idiopidae")

def tokenize(lexer, text):
    """
    For debugging. Returns array of strings with info on each token.
    """
    lexer.input(text)
    token_info = []
    while True:
        tok = lexer.token()
        if not tok: break      # No more input
        token_info.append("%03d %-15s %s" % (tok.lexpos, tok.type, tok.value.replace("\n","")))
    return token_info

def parse_input(text, log):
    global sections
    global level

    # clean out any old content
    for k in sections.keys():
        del sections[k]
    assert len(sections) == 0

    level = 0
    start_new_section(0, 0, level)

    lexer = lex.lex(errorlog=log)

    parser = yacc.yacc(debug=0, debuglog=log, tabmodule="foo", outputdir='logs')
    parser.parse(text, lexer=lexer)

    return sections

from dexy.filters.pyg import PygmentsFilter
from pygments import highlight

class Id(PygmentsFilter):
    """
    Id filter.
    """
    aliases = ['idio', 'id']
    _settings = {
            'remove-leading-empty-anonymous-section' : ("If a document starts with empty section named '1', remove it.", False),
            'output-data-type' : 'sectioned',
            'output-extensions' : PygmentsFilter.MARKUP_OUTPUT_EXTENSIONS + PygmentsFilter.IMAGE_OUTPUT_EXTENSIONS + [".txt"]
            }

    def process(self):
        global remove_leading_empty_anonymous_section
        lexer = self.create_lexer_instance()
        formatter = self.create_formatter_instance()
        output = OrderedDict()
        input_text = self.input_data.as_text()
        remove_leading_empty_anonymous_section = self.setting('remove-leading-empty-anonymous-section')
        for k, v in parse_input(input_text, self.doc.wrapper.log).iteritems():
            output[k] = highlight(v['contents'], lexer, formatter)
        self.output_data.set_data(output)
