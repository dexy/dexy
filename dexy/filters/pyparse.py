from dexy.filter import DexyFilter
from lib2to3.pytree import Leaf
import inspect
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
            'string-types' : ("Token types corresponding to strings.", (3,)),
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
            for name, val in python_symbols.__dict__.items():
                if type(val) == int:
                    self._type_reprs[val] = name
        return self._type_reprs.setdefault(type_num, type_num)

    def type_of(self, node):
        return self.type_repr(node.type)

    def eval_string(self, leaf):
        return eval(leaf.value).strip()

    def first_simple_statement_after_any_whitespace(self, parent):
        for child in parent.children:
            if child.type in self.setting('whitespace-types'):
                pass
            elif child.type in self.setting('string-types'):
                first_child = child
                return self.eval_string(first_child)
            elif self.type_of(child) == "simple_stmt":
                first_child = child.children[0]
                if isinstance(first_child, Leaf) and first_child.type in self.setting('string-types'):
                    return self.eval_string(first_child)

    def process_node(self, node, prefix):
        node_type = self.type_of(node)

        decorators = []
        if node_type == 'decorated':
            # are we a decorated function or a decorated class?
            for child in node.children:
                if self.type_of(child) == "decorator":
                    decorators.append(str(child).rstrip())
                elif self.type_of(child) == "decorators":
                    for decorator in child.children:
                        decorators.append(str(decorator).rstrip())
                else:
                    child_type = self.type_of(child)
                    if child_type == "funcdef":
                        self.process_function(node, prefix, decorators)
                    elif child_type == "classdef":
                        self.process_class(node, prefix, decorators)
                    else:
                        raise Exception("unknown decorated child type '%s'" % child_type)

        elif node_type == 'funcdef':
            return self.process_function(node, prefix, decorators)
        elif node_type == "classdef":
            return self.process_class(node, prefix, decorators)
        elif node_type == 'simple_stmt':
            return self.process_simple_stmt(node, prefix, decorators)
        else:
            return prefix

    def process_root(self, node, prefix):
        docstring = self.first_simple_statement_after_any_whitespace(node)
        if prefix is None:
            key = ":doc"
        elif "None" in prefix:
            key = ":doc"
        else:
            key = "%s:doc" % prefix
   
        not_already_in_keys = not key in list(self.output_data.keys())
        is_a_docstring = docstring is not None
        if not_already_in_keys and is_a_docstring:
            self.output_data.append(key, inspect.cleandoc(docstring))

        self.process_node(node, prefix)

    def process(self):
        self.func_name = None
        self.class_name = None
        self.setup_driver()

        text = str(self.input_data)

        if text == "None":
            self.output_data.set_data({})
        else:
            root = self.driver.parse_string(text)

            for node in root.children:
                self.process_root(node, None)

            self.output_data.save()

    def name_with_prefix(self, name, prefix):
        if prefix is None:
            return name
        else:
            return "%s.%s" % (prefix, name)

    def process_function(self, node, prefix, decorators):
        def process_func_part(state, part):
            if state == "def":
                assert isinstance(part, Leaf) and part.value == "def", part
                return "funcname"
    
            elif state == "funcname":
                assert isinstance(part, Leaf) and part.type == 1
                self.func_name = part.value

                name_with_prefix = self.name_with_prefix(self.func_name, prefix)
                raw_source = str(node).rstrip().splitlines()

                is_function_started = False
                leading_comments = []
                source_lines = []
                indent = None
                for line in raw_source:
                    is_comment = line.lstrip().startswith("#")
                    is_decorator = line.lstrip().startswith("@")
                    has_def = "def" in line

                    if has_def and indent is None:
                        indent = len(line) - len(line.lstrip())

                    if is_function_started:
                        source_lines.append(line)

                    elif not is_function_started and is_comment:
                        leading_comments.append(line)

                    elif not is_comment and (has_def or is_decorator):
                        is_function_started = True
                        source_lines.append(line)
                  
                # Strip trailing comments and empty lines.
                while source_lines[-1].lstrip().startswith("#") or not source_lines[-1].lstrip():
                    source_lines.pop()

                # Fix decorator indent.
                for i, line in enumerate(source_lines):
                    if not line.startswith("@"):
                        break
                    if len(line) - len(line.lstrip()) == 0 and indent > 0:
                        source_lines[i] = " " * indent + line

                self.output_data.append("%s:source" % name_with_prefix, "\n".join(source_lines))
                self.output_data.append("%s:decorators" % name_with_prefix, "\n".join(decorators))
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
                if docstring is not None:
                    self.output_data.append("%s:doc" % self.name_with_prefix(self.func_name, prefix), inspect.cleandoc(docstring))
    
            elif state is None:
                pass
    
            else:
                raise Exception("invalid state '%s'" % state)
    
        state = "def"
        for child in node.children:
            if self.type_of(child) in ("decorator", "decorators",):
                pass
            elif self.type_of(child) == "funcdef":
                for grandchild in child.children:
                    state = process_func_part(state, grandchild)
                    if state == None:
                        break
            else:
                state = process_func_part(state, child)
                if state is None:
                    break
    
        name_with_prefix = self.name_with_prefix(self.func_name, prefix)
        self.func_name = None
        return name_with_prefix
    
    def process_class(self, node, prefix, decorators):
        def process_class_part(state, part):
            if state == "class":
                assert isinstance(part, Leaf) and part.value == "class"
                return "classname"
    
            elif state == "classname":
                assert isinstance(part, Leaf) and part.type == 1
                self.class_name = part.value
                name_with_prefix = self.name_with_prefix(self.class_name, prefix)
                self.output_data.append("%s:source" % name_with_prefix, str(node).strip())
                return "parameters"
    
            elif state == "parameters":
                if isinstance(part, Leaf) and part.value == ":":
                    return "body"
                else:
                    # continue processing parameters
                    return "parameters"
    
            elif state == "body":
                assert self.type_of(part) == "suite"

                # Parse any Class docstring
                name_with_prefix = self.name_with_prefix(self.class_name, prefix)
                docstring = self.first_simple_statement_after_any_whitespace(part)
                if docstring is not None:
                    self.output_data.append("%s:doc" % name_with_prefix, inspect.cleandoc(docstring))
   
                # Parse class and instance methods
                for child in part.children:
                    if self.type_of(child) in ('funcdef', 'decorated'):
                        self.process_node(child, self.name_with_prefix(self.class_name, prefix))
    
            else:
                raise Exception("invalid state '%s'" % state)
    
        state = "class"
        for child in node.children:
            if self.type_of(child) in ("decorator", "decorators",):
                pass
            elif self.type_of(child) == "classdef":
                for grandchild in child.children:
                    state = process_class_part(state, grandchild)
                    if state == None:
                        break
            else:
                state = process_class_part(state, child)
                if state is None:
                    break
   
        name_with_prefix = self.name_with_prefix(self.class_name, prefix)
        self.class_name = None
        return name_with_prefix

    def process_simple_stmt(self, node, prefix, decorators):
        for child in node.children:
            child_type = self.type_of(child)
            if child_type == "expr_stmt":
                if isinstance(child.children[0], Leaf):
                    name_leaf = child.children[0]
                    name = name_leaf.value
                    self.output_data.append("%s:source" % name, str(child))
                else:
                    # print "complex expr_stmt"
                    pass
            else:
                #print "unknown child type '%s'" % child_type
                pass
