from dexy.common import OrderedDict
from dexy.exceptions import UserFeedback
from dexy.filters.pyg import PygmentsFilter
from pygments import highlight
import ply.lex as lex
import ply.yacc as yacc

class Id(PygmentsFilter):
    """
    Filter for splitting text files into sections based on specially-formatted
    comments. Replacement for idiopidae.

    For more information about the settings starting with ply-, see the PLY
    YACC parser documentation http://www.dabeaz.com/ply/ply.html#ply_nn36
    """
    aliases = ['idio', 'id', 'idiopidae']
    _settings = {
            'remove-leading' : ("If a document starts with empty section named '1', remove it.", False),
            'ply-debug' : ("The 'debug' setting to pass to PLY. A setting of 1 will produce very verbose output.", 0),
            'ply-optimize' : ("Whether to use optimized mode for the lexer.", 1),
            'ply-write-tables' : ("Whether to generate parser table files (which will be stored in ply-outputdir and named ply-tabmodule).", 1),
            'ply-outputdir' : ("Location relative to where you run dexy in which ply will store table files. Defaults to dexy's log directory.", None),
            'ply-parsetab' : ("Name of parser tabfile (.py extension will be added) to be stored in ply-outputdir if ply-write-tables set to 1.", 'id_parsetab'),
            'ply-lextab' : ("Name of lexer tabfile (.py extension will be added) to be stored in ply-outputdir if ply-optimize is set to 1.", 'id_lextab'),
            'output-extensions' : PygmentsFilter.MARKUP_OUTPUT_EXTENSIONS + PygmentsFilter.IMAGE_OUTPUT_EXTENSIONS
            }

    def process(self):
        input_text = self.input_data.as_text()
        output = OrderedDict()

        settings = self.setting_values()
        if not settings['ply-outputdir']:
            settings['ply-outputdir'] = self.doc.wrapper.log_dir

        id_parser = IdParser(settings, self.doc.wrapper.log)

        pyg_lexer = self.create_lexer_instance()
        pyg_formatter = self.create_formatter_instance()

        for k, v in id_parser.parse(input_text).iteritems():
            output[k] = highlight(v['contents'], pyg_lexer, pyg_formatter)

        self.output_data.set_data(output)

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

class IdParser(object):
    tokens = tokens
    states = states

    def __init__(self, settings, log):
        self.settings = settings
        self.log = log

    def setup(self):
        self.sections = OrderedDict()
        self.level = 0
        self.start_new_section(0, 0, self.level)

        lexer_kwargs = {
                'optimize' : self.settings['ply-optimize'],
                'outputdir' : self.settings['ply-outputdir'],
                'lextab' : self.settings['ply-lextab']
                }

        parser_kwargs = {
                'debug' : self.settings['ply-debug'],
                'write_tables' : self.settings['ply-write-tables'],
                'outputdir' : self.settings['ply-outputdir'],
                'tabmodule' : self.settings['ply-parsetab']
                }

        self.lexer = lex.lex(module=self, errorlog=self.log, **lexer_kwargs)
        self.parser = yacc.yacc(module=self, debuglog=self.log, **parser_kwargs)

    def append_text(self, code):
        """
        Append to the currently active section.
        """
        self.set_current_section_contents(self.current_section_contents() + code)
    
    def current_section_exists(self):
        return len(self.sections) > 0
    
    def current_section_key(self):
        return self.sections.keys()[-1]
    
    def current_section_contents(self):
        return self.sections[self.current_section_key()]['contents']
    
    def current_section_empty(self):
        return len(self.current_section_contents()) == 0
    
    def set_current_section_contents(self, text):
        self.sections[self.current_section_key()]['contents'] = text
   
    def strip_trailing_newline(self):
        self.set_current_section_contents(self.current_section_contents().rsplit("\n",1)[0])

    def start_new_section(self, position, lineno, new_level, name=None):
        if name:
            if self.settings['remove-leading']:
                if len(self.sections) == 1 and self.current_section_empty():
                    del self.sections[u'1']
        else:
            # Generate anonymous section name.
            name = unicode(len(self.sections)+1)
    
        try:
            self.change_level(new_level)
        except Exception as e:
            print name
            raise e
    
        self.sections[name.rstrip()] = {
                'position' : position,
                'lineno' : lineno,
                'contents' : u'',
                'level' : self.level
                }
    
    def change_level(self, new_level):
        if new_level == self.level:
            pass
        elif new_level < self.level:
            pass
        elif new_level == self.level + 1:
            pass
        elif new_level > (self.level + 1):
            msg = "attempting to indent more than 1 level to %s from previous level %s"
            msgargs = (new_level, self.level)
            raise Exception(msg % msgargs)
        elif new_level < 0:
            raise Exception("attepmting to indent to level below 0, does not exist")
        else:
            msg = "logic error! new level %s current level %s"
            msgargs = (new_level, self.level)
            raise Exception(msg % msgargs)
    
        self.level = new_level
    
    def next_char(self, t):
        return t.lexer.lexdata[t.lexer.lexpos:t.lexer.lexpos+1]

    def lookahead_n(self, t, n):
        # TODO what if n is too big?
        return t.lexer.lexdata[t.lexer.lexpos:t.lexer.lexpos+n]

    def lookahead_for(self, t, word):
        return self.lookahead_n(t, len(word)) == word

    def lookahead_for_any(self, t, words):
        any_found = False
        for word in words:
            if self.lookahead_for(t, word):
                any_found = True
                break
        return any_found
   
    # Lexer tokens for idio state
    def t_idio_AT(self, t):
        r'@'
        return t
    
    def t_idio_AMP(self, t):
        r'&'
        return t
    
    def t_idio_COLONS(self, t):
        r':+'
        return t
    
    def t_idio_DBLQUOTE(self, t):
        r'"'
        return t
    
    def t_idio_SGLQUOTE(self, t):
        r'\''
        return t
    
    def t_idio_EXP(self, t):
        r'export|section'
        return t
    
    def t_idio_END(self, t):
        r'end'
        return t
    
    def t_idio_WHITESPACE(self, t):
        r'(\ |\t)+'
        return t
    
    def t_idio_NEWLINE(self, t):
        r'\r\n|\n|\r'
        if not t.lexer.idio_expect_closing_block:
            t.lexer.pop_state()
        t.lexer.pop_state()
        return t
   
    def t_idio_IDIOCLOSE(self, t):
        r'(-->)|(\*/)'
        if not t.lexer.idio_expect_closing_block:
            raise UserFeedback("Unexpected code %s in an idio block" % t.value)
        return t

    def t_idio_WORD(self, t):
        r'[a-zA-Z-]+'
        return t
    
    # Lexer tokens and helpers for idiostart state
    def idiostart_incr_comment(self, t):
        if t.lexer.comment_char == t.value:
            t.lexer.comment_char_count += 1
        else:
            return self.idiostart_abort(t)
    
    def idiostart_abort(self, t):
        t.value = t.lexer.lexdata[t.lexer.comment_start_pos:t.lexer.lexpos]
        t.type = "CODE"
        t.lexer.pop_state()
        return t
   
    def t_idiostart_COMMENT(self, t):
        r'\#|%|/'
        return self.idiostart_incr_comment(t)
    
    def t_idiostart_SPACE(self, t):
        r'\ +'
        if t.lexer.comment_char_count != 3:
            return self.idiostart_abort(t)
        else:   
            t.lexer.push_state('idio')
            t.value = t.lexer.lexdata[t.lexer.comment_start_pos:t.lexer.lexpos]
            t.type = 'IDIO'
            return t
    
    def t_idiostart_ABORT(self, t):
        r'[^#/% ]'
        return self.idiostart_abort(t)
  
    # Lexer tokens and helpers for initial state
    def start_idiostart(self, t):
        if self.next_char(t) == '\n':
            t.type = 'CODE'
            return t
        else:
            t.lexer.comment_char = t.value
            t.lexer.comment_char_count = 1
            t.lexer.comment_start_pos = t.lexer.lexpos - 1
            t.lexer.idio_expect_closing_block = False
            t.lexer.push_state('idiostart')

    def t_IDIOOPEN(self, t):
        r'(<!--|/\*\*\*)\ +@'
        if self.lookahead_for_any(t, ['export', 'section', 'end']):
            t.lexer.push_state('idio')
            t.lexer.idio_expect_closing_block = True
            return t
        else:
            t.type = 'CODE'
            return t
    
    def t_COMMENT(self, t):
        r'\#|%|/'
        return self.start_idiostart(t)

    def t_NEWLINE(self, t):
        r'\r\n|\n|\r'
        return t
    
    def t_WHITESPACE(self, t):
        r'[\ \t]+'
        return t
    
    def t_CODE(self, t):
        r'[^\#/\n\r]+'
        return t
    
    def p_main(self, p):
        '''entries : entries entry
                   | entry'''
        pass
    
    def p_entry(self, p):
        '''entry : NEWLINE
                 | codes NEWLINE
                 | codes inlineidio NEWLINE
                 | idioline NEWLINE'''
        p.lexer.lineno += 1
        if len(p) == 2:
            self.append_text('\n')
        elif len(p) == 3:
            if p[1]:
                self.append_text(p[1] + '\n')
            pass
        elif len(p) == 4:
            code_content = p[1]
            self.append_text(code_content + "\n")
            # TODO Process inlineidio directives @elide &tag
            # inlineidio_content = p[2]
        else:
            raise Exception("unexpected length " + len(p))
    
    def p_codes(self, p):
        '''codes : codes codon
                 | codon'''
        if len(p) == 2:
            p[0] = p[1]
        elif len(p) == 3:
            if p[1]:
                p[0] = p[1] + p[2]
            else:
                p[0] = p[2]
    
    def p_codon(self, p):
        '''codon : CODE 
                 | WHITESPACE'''
        p[0] = p[1]
    
    def p_inlineidio(self, p):
        '''inlineidio : IDIO AMP WORD'''
        p[0] = p[1] + p[2] + p[3]
    
    def p_idioline(self, p):
        '''idioline : idio
                    | idio WHITESPACE
                    | WHITESPACE idio
                    | WHITESPACE idio WHITESPACE'''
        pass
    
    def p_linecontent(self, p):
        '''idio : export
                | exportq
                | exportql
                | sectionstart
                | closedcomment
                | closedcommentlevels
                | end '''
        pass
    
    ## Methods Defining Section Boundaries
    def p_sectionstart(self, p):
        '''sectionstart : IDIO WORD
                        | IDIO COLONS WORD'''
        if len(p) == 3:
            # no colons, so level is 0
            self.start_new_section(p.lexpos(1), p.lineno(1), 0, p[2])
        elif len(p) == 4:
            self.start_new_section(p.lexpos(1), p.lineno(1), len(p[2]), p[3])
        else:
            raise Exception("unexpected length %s" % len(p))
   
    def p_closed_comment(self, p):
        '''closedcomment : IDIOOPEN EXP WHITESPACE WORD IDIOCLOSE
                         | IDIOOPEN EXP WHITESPACE WORD WHITESPACE IDIOCLOSE'''
        assert len(p) in [6,7]
        self.start_new_section(p.lexpos(1), p.lineno(1), 0, p[4])

    def p_closed_comment_levels(self, p):
        '''closedcommentlevels : IDIOOPEN EXP WHITESPACE COLONS WORD IDIOCLOSE
                               | IDIOOPEN EXP WHITESPACE COLONS WORD WHITESPACE IDIOCLOSE'''
        assert len(p) in [7,8]
        self.start_new_section(p.lexpos(1), p.lineno(1), len(p[4]), p[5])

    ## Old Idiopidae @export syntax
    def p_export(self, p):
        '''export : IDIO AT EXP WHITESPACE words
                  | IDIO AT EXP WHITESPACE words WHITESPACE'''
        assert len(p) in [6,7]
        self.start_new_section(p.lexpos(1), p.lineno(1), 0, p[5])
    
    def p_export_quoted(self, p):
        '''exportq : IDIO AT EXP WHITESPACE quote words quote
                   | IDIO AT EXP WHITESPACE quote words quote WHITESPACE'''
        assert len(p) in [8,9]
        self.start_new_section(p.lexpos(1), p.lineno(1), 0, p[6])
    
    def p_export_quoted_with_language(self, p):
        '''exportql : IDIO AT EXP WHITESPACE quote words quote WHITESPACE words
                    | IDIO AT EXP WHITESPACE quote words quote WHITESPACE words WHITESPACE'''
        assert len(p) in [10,11]
        self.start_new_section(p.lexpos(1), p.lineno(1), 0, p[6])
    
    def p_end(self, p):
        '''end : IDIO AT END
               | IDIOOPEN END IDIOCLOSE
               | IDIOOPEN END WHITESPACE IDIOCLOSE'''
        self.start_new_section(p.lexpos(1), p.lineno(1), self.level)
    
    def p_quote(self, p):
        '''quote : DBLQUOTE
                 | SGLQUOTE'''
        p[0] = p[1]
    
    def p_words(self, p):
        '''words : words WHITESPACE WORD
                 | WORD'''
        if len(p) == 4:
            p[0] = p[1] + p[2] + p[3]
        elif len(p) == 2:
            p[0] = p[1]
        else:
            raise Exception("unexpected length %s" % len(p))
    
    def p_error(self, p):
        if not p:
            raise UserFeedback("Reached EOF when parsing file using idioipdae.")
        raise UserFeedback("Unable to parse at token %s" % p)
   
    def tokenize(self, text):
        """
        Return array of lexed tokens (for debugging).
        """
        self.setup()
        self.lexer.input(text)
        tokens = []
        while True:
            tok = self.lexer.token()
            if not tok: break      # No more input
            tokens.append(tok)
        return tokens
   
    def token_info(self, text):
        """
        Returns debugging information about lexed tokens as a string.
        """
        def tok_info(tok):
            return "%03d %-15s %s" % (tok.lexpos, tok.type, tok.value.replace("\n",""))
        return "\n".join(tok_info(tok) for tok in self.tokenize(text))

    def parse(self, text):
        """
        Run the parser on the text passed in, returns OrderedDict structure.
        """
        self.setup()

        # Parser requires content to end with newline - add one and then strip
        # from final section.
        self.parser.parse(text + "\n", lexer=self.lexer)
        self.strip_trailing_newline()

        return self.sections
