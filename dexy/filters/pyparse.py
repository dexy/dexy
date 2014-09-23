from dexy.filter import DexyFilter
import lib2to3.pgen2.driver
import lib2to3.pytree
import os

driver_file = lib2to3.pgen2.driver.__file__
grammar_dir = os.path.abspath(os.path.join(os.path.dirname(driver_file), ".."))

class PyParse(DexyFilter):
    """
    Parses Python source code using lib2to3, without loading files, so doesn't
    cause side effects or care if imports work.
    """
    aliases = ['pyparse']

    _settings = {
            'data-type' : 'keyvalue',
            'whitespace-types' : ("Token types corresponding to whitespace.", (4, 5)),
            'grammar-file' : ("Name or full path to file specifying Python language grammar.", "Grammar.txt")
            }

    def grammar_path(self):
        grammar_file = self.setting('grammar-file')
        if "/" in grammar_file:
            return grammar_file
        else:
            return os.path.join(grammar_dir, grammar_file)

    def setup_driver(self):
        self.grammar = lib2to3.pgen2.driver.load_grammar(self.grammar_path())
        self.driver = lib2to3.pgen2.driver.Driver(self.grammar, convert=lib2to3.pytree.convert)

    def type_repr(self, type_num):
        if not hasattr(self, "_type_reprs"):
            from lib2to3.pygram import python_symbols
            self._type_reprs = {}
            for name, val in python_symbols.__dict__.iteritems():
                if type(val) == int:
                    self._type_reprs[val] = name
        return self._type_reprs.setdefault(type_num, type_num)

    def type_of(self, node):
        return self.type_repr(node.type)

    def first_simple_statement_after_any_whitespace(self, parent):
        for child in parent.children:
            if child.type in self.setting('whitespace-types'):
                pass
            elif child.type == 3:
                first_child = child
                return eval(first_child.value).strip()
            elif self.type_of(child) == "simple_stmt":
                first_child = child.children[0]
                return eval(first_child.value).strip()
            else:
                return

    def process_node(self, node, prefix):
        node_type = self.type_of(node)
        if node_type == "funcdef":
            return self.process_function(node, prefix)
        elif node_type == "classdef":
            return self.process_class(node, prefix)
        else:
            return (prefix, False)

    def process_root(self, node, prefix):
        docstring = self.first_simple_statement_after_any_whitespace(node)

        if prefix is None:
            key = ":doc"
        elif "None" in prefix:
            key = ":doc"
        else:
            key = "%s:doc" % prefix
    
        if not key in self.output_data.keys():
            self.output_data.append(key, docstring)

        prefix, recurse = self.process_node(node, prefix)
        if recurse:
            for child in node.children:
                self.process_root(child, prefix)

    def process(self):
        self.func_name = None
        self.class_name = None
        self.setup_driver()

        text = unicode(self.input_data)
        root = self.driver.parse_string(text)
        
        for node in root.children:
            self.process_root(node, None)

        self.output_data.save()

    def name_with_prefix(self, name, prefix):
        if prefix is None:
            return name
        else:
            return "%s.%s" % (prefix, name)

    def process_function(self, node, prefix):
        state = "def"
    
        def process_func_part(state, part):
            if state == "def":
                if part.value == "def":
                    return "funcname"
                else:
                    raise Exception("Was expecting 'def' got '%s'" % part.value)
    
            elif state == "funcname":
                self.func_name = part.value
                source = "\n".join(decorators) + str(node).strip()
                self.output_data.append("%s:source" % self.name_with_prefix(self.func_name, prefix), source)
                return "parameters"
    
            elif state == "parameters":
                assert self.type_of(part) == "parameters"
                return "colon"
    
            elif state == "colon":
                assert part.value == ":"
                return "body"
    
            elif state == "body":
                assert self.type_of(part) == "suite"
                docstring = self.first_simple_statement_after_any_whitespace(part)
                self.output_data.append("%s:doc" % self.name_with_prefix(self.func_name, prefix), docstring)
    
            elif state is None:
                pass
    
            else:
                raise Exception("invalid state '%s'" % state)
    
        decorators = []
        for child in node.children:
            if self.type_of(child) == "decorator":
                decorators.append(str(child).strip())
            elif self.type_of(child) == "funcdef":
                for grandchild in child.children:
                    state = process_func_part(state, grandchild)
                    if state == None:
                        break
            else:
                state = process_func_part(state, child)
                if state is None:
                    break
    
        if self.func_name is None:
            raise Exception("func name is none")
        else:
            augmented_name = self.name_with_prefix(self.func_name, prefix)
            self.func_name = None
            return augmented_name, False
    
    def process_class(self, node, prefix):
        state = "class"
    
        def process_class_part(state, part):
            global class_name
            if state == "class":
                if part.value == "class":
                    return "classname"
                else:
                    raise Exception("Was expecting 'class' got '%s'" % part.value)
    
            elif state == "classname":
                class_name = part.value
                self.output_data.append("%s:source" % self.name_with_prefix(class_name, prefix), str(node).strip())
                return "parameters"
    
            elif state == "parameters":
                if part.value == ":":
                    return "body"
                else:
                    return "parameters"
    
            elif state == "body":
                assert self.type_of(part) == "suite"
                self.output_data.append("%s:doc" % self.name_with_prefix(class_name, prefix), self.first_simple_statement_after_any_whitespace(part))
    
                for child in part.children:
                    if self.type_of(child) in ("funcdef", "decorated"):
                        self.process_function(child, self.name_with_prefix(class_name, prefix))
    
            elif state is None:
                pass
    
            else:
                raise Exception("invalid state '%s'" % state)
    
        for child in node.children:
            state = process_class_part(state, child)
            if state is None:
                break
    
        return self.name_with_prefix(prefix, self.class_name), True
