"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
from VMWriter import *
from SymbolTable import *

# try
CONVERT_KIND = {
    'ARG': 'ARG',
    'STATIC': 'STATIC',
    'VAR': 'LOCAL',
    'FIELD': 'THIS'
}


class CompilationEngine:
    """Gets input from a JackTokenizer and emits its parsed structure into an
    output stream.
    """

    def __init__(self, input_stream: "JackTokenizer", output_stream) -> None:
        """
        Creates a new compilation engine with the given input and output. The
        next routine called must be compileClass()
        :param input_stream: The input stream.
        :param output_stream: The output stream.
        """
        # Your code goes here!
        # Note that you can write to output_stream like so:
        # output_stream.write("Hello world! \n")
        self.if_labels_count = 0
        self._class_name = ""
        self._output_stream = output_stream
        self._input_stream = input_stream
        self.VMWriter = VMWriter(output_stream)
        self.type_dict = {"KEYWORD": "keyword", "SYMBOL": "symbol",
                          "INT_CONST": "integerConstant",
                          "STRING_CONST": "stringConstant",
                          "IDENTIFIER": "identifier"}
        # self.binary_op = {'+', '-', '*', '/', '|', '=', '&lt;', '&gt;',
        #                   '&amp;'}
        self.binary_op_dct = {'+': '+', '-': '-', '*': '*', '/': '/', '|': '|',
                              '=': '=', '<': '&lt;', '>': '&gt;', '&': '&amp;'}
        self.unary_op = {'-', '~', '^', '#'}

        self.binary_op_dct_vm = {'+': 'ADD', '-': 'SUB', '*': '*', '/': '/',
                                 '|': 'OR',
                                 '=': 'EQ', '<': 'LT', '>': 'GT',
                                 '&': 'AND'}
        self.unary_op_vm = {'-': 'NEG', '~': 'NOT', '^': 'SHIFTLEFT',
                            '#': 'SHIFRIGHT'}

        self.keyword_constant = {'true', 'false', 'null', 'this'}
        self.keyword_constant_dct = {'true': ['CONST', 0],
                                     'false': ['CONST', 0],
                                     'null': ['CONST', 0],
                                     'this': ['POINTER', 0]}
        self.classVarDec = ['static', 'field']
        self.subroutineDec = ['constructor', 'method', 'function']
        self.symbol_table = SymbolTable()
        self.while_labels_count = 0

    def compile_class(self) -> None:
        """Compiles a complete class."""
        # Your code goes here!
        self.write_xml_tag("class")

        self.write_token()  # class
        self._class_name = self._input_stream.cur_token()
        self.write_token()  # class_name
        self.write_token()  # {

        while self._input_stream.cur_token() in self.classVarDec \
                or self._input_stream.cur_token() in self.subroutineDec:
            if self._input_stream.cur_token() in self.classVarDec:
                self.compile_class_var_dec()
            elif self._input_stream.cur_token() in self.subroutineDec:
                self.compile_subroutine()

        self.write_token()  # }
        self.write_xml_tag("class", True)

    def compile_class_var_dec(self) -> None:
        """Compiles a static declaration or a field declaration."""
        # Your code goes here!
        self._output_stream.write("<classVarDec>\n")
        kind = self._input_stream.cur_token().upper()
        self.write_token()  # static or field
        type = self._input_stream.cur_token().upper()
        self.write_token()  # var type
        name = self._input_stream.cur_token()
        self.write_token()  # var name
        self.symbol_table.define(name, type, kind)
        while self._input_stream.cur_token() == ",":
            self.write_token()  # ","
            name = self._input_stream.cur_token()
            self.write_token()  # var name
            self.symbol_table.define(name, type, kind)
        self.write_token()  # ;

        self._output_stream.write("</classVarDec>\n")

    def compile_subroutine(self) -> None:
        """
        Compiles a complete method, function, or constructor.
        You can assume that classes with constructors have at least one field,
        you will understand why this is necessary in project 11.
        """
        # Your code goes here!
        # Your code goes here!

        self.write_xml_tag("subroutineDec")

        self.symbol_table.start_subroutine()
        func_type = self._input_stream.cur_token()
        if func_type == "method":  # add this 0
            self.symbol_table.define('this', self._class_name, 'ARG')

        self.write_token()  # get field \ method \ contracture
        self.write_token()  # get subroutine return type \ 'constructor'
        sub_name = self._input_stream.cur_token()
        func_name = self._class_name + '.' + sub_name
        self.write_token()  # get subroutine name \ 'new'
        self.write_token()  # get '(' symbol
        self.compile_parameter_list()
        self.write_token()  # get ')' symbol
        self.compile_subroutine_body(func_type, func_name)
        # self.write_token() #'}'
        self.write_xml_tag("subroutineDec", True)

    def compile_subroutine_body(self, func_type, name):
        self.write_xml_tag("subroutineBody")
        self.write_token()  # '{'
        while self._input_stream.cur_token() == 'var':
            self.compile_var_dec()
        vars = self.symbol_table.var_count('VAR')
        self.VMWriter.write_function(name, vars)
        if func_type == 'method':
            # Save self at pointer
            self.VMWriter.write_push('ARG', 0)
            self.VMWriter.write_pop('POINTER', 0)
        if func_type == 'contracture':
            # Memory allocates for all fields
            fields = self.symbol_table.var_count('FIELD')
            self.VMWriter.write_push('CONST', fields)
            self.VMWriter.write_call('Memory.alloc', 1)
            # Save allocated memory at pointer
            self.VMWriter.write_pop('POINTER', 0)
        self.compile_statements()
        self.write_token()  # '}'
        self.write_xml_tag("subroutineBody", True)

    def compile_parameter_list(self) -> None:
        """Compiles a (possibly empty) parameter list, not including the 
        enclosing "()".
        """
        # Your code goes here!
        params = 0
        self.write_xml_tag("parameterList")
        if self._input_stream.cur_token() != ")":
            params += 1
            type = self._input_stream.cur_token().upper()
            self.write_token()  # type
            name = self._input_stream.cur_token()
            self.symbol_table.define(name, type, 'ARG')
            self.write_token()  # name
            while self._input_stream.cur_token() == ',':
                self.write_token()  # ","
                type = self._input_stream.cur_token().upper()
                self.write_token()  # type
                name = self._input_stream.cur_token()
                self.symbol_table.define(name, type, 'ARG')
                self.write_token()  # name

        self.write_xml_tag("parameterList", True)

    def compile_var_dec(self) -> None:
        """Compiles a var declaration."""
        # Your code goes here!
        self.write_xml_tag("varDec")
        self.write_token()  # var
        type = self._input_stream.cur_token().upper()
        self.write_token()  # type

        names = []
        names.append(self._input_stream.cur_token())
        self.write_token()  # var name
        while self._input_stream.cur_token() == ',':
            self.write_token()  # ","
            names.append(self._input_stream.cur_token())
            self.write_token()  # var name
        self.write_token()  # ';'

        for name in names:
            self.symbol_table.define(name, type, 'VAR')

        self.write_xml_tag("varDec", True)

    def compile_statements(self) -> None:
        """Compiles a sequence of statements, not including the enclosing 
        "{}".
        """
        # Your code goes here!
        self.write_xml_tag("Statement")
        while self._input_stream.cur_token() in {"let", "if", "while", "do",
                                                 "return"}:
            if self._input_stream.cur_token() == "let":
                self.compile_let()
            elif self._input_stream.cur_token() == "if":
                self.compile_if()
            elif self._input_stream.cur_token() == "while":
                self.compile_while()
            elif self._input_stream.cur_token() == "do":
                self.compile_do()
            elif self._input_stream.cur_token() == "return":
                self.compile_return()
        self.write_xml_tag("Statement", True)

    def compile_do(self):
        self.write_xml_tag("doStatement")
        self.write_token()  # do
        identifier = self._input_stream.cur_token()
        self.write_token()  # identifier
        self.compile_subroutine_call(identifier)
        self.VMWriter.write_pop("TEMP", 0)
        self.write_token()  # ';'
        self.write_xml_tag("doStatement", True)

    def compile_let(self) -> None:
        """Compiles a let statement."""
        # Your code goes here!
        self.write_xml_tag("letStatement")
        is_array = False
        self.write_token()  # let
        var_name = self._input_stream.cur_token()
        var_kind = self.symbol_table.kind_of(var_name)
        var_index = self.symbol_table.index_of(var_name)
        self.write_token()  # varName
        if self._input_stream.cur_token() == "[":
            is_array = True
            self.write_token()  # [
            self.compile_expression()
            self.write_token()  # ]

            self.VMWriter.write_push(CONVERT_KIND[var_kind], var_index)
            self.VMWriter.write_arithmetic("ADD")

        self.write_token()  # =
        self.compile_expression()
        self.write_token()  # ;
        if is_array:

            self.VMWriter.write_pop("TEMP", 0)
            self.VMWriter.write_pop("POINTER", 1)
            self.VMWriter.write_push("TEMP", 0)
            self.VMWriter.write_pop("THAT", 0)
        else:
            self.VMWriter.write_pop(CONVERT_KIND[var_kind], var_index)
        self.write_xml_tag("letStatement", True)

    def compile_while(self) -> None:
        """Compiles a while statement."""
        # Your code goes here!
        self.write_xml_tag("whileStatement")
        while_labels_count = self.while_labels_count
        self.while_labels_count += 1
        self.VMWriter.write_label(f"WHILE_EXP{while_labels_count}")
        self.write_token()  # while
        self.write_token()  # (
        self.compile_expression()
        self.write_token()  # )

        self.VMWriter.write_arithmetic("NOT")
        self.VMWriter.write_if(f"WHILE_END{while_labels_count}")
        self.write_token()  # {


        self.compile_statements()
        self.VMWriter.write_goto(f"WHILE_EXP{while_labels_count}")
        self.VMWriter.write_label(f"WHILE_END{while_labels_count}")

        self.write_token()  # }
        self.write_xml_tag("whileStatement", True)

    def compile_return(self) -> None:
        """Compiles a return statement."""
        # Your code goes here!
        self.write_xml_tag("returnStatement")
        self.write_token()  # return
        if self._input_stream.cur_token() != ';':
            while self._input_stream.cur_token() != ';':
                self.compile_expression()
        else:
            self.VMWriter.write_push('CONST', 0)
        self.write_token()  # ';'
        self.VMWriter.write_return()
        self.write_xml_tag("returnStatement", True)

    def compile_if(self) -> None:
        """Compiles a if statement, possibly with a trailing else clause."""
        # Your code goes here!
        self.write_xml_tag("ifStatement")
        if_labels_count = self.if_labels_count
        self.write_token()  # if
        self.write_token()  # (
        self.compile_expression()
        self.write_token()  # )
        self.VMWriter.write_arithmetic("NEG")
        self.VMWriter.write_if(f"IF_FALSE{if_labels_count}")

        self.VMWriter.write_goto(f"IF_END{if_labels_count}")

        self.VMWriter.write_label(f"IF_FALSE{if_labels_count}")
        self.write_token()  # {
        self.compile_statements()
        self.write_token()  # }

        if self._input_stream.cur_token() == "else":
            self.write_token()  # else
            self.write_token()  # {
            self.compile_statements()
            self.write_token()  # }
        self.VMWriter.write_label(f"IF_END{if_labels_count}")
        self.if_labels_count += 1
        self.write_xml_tag("ifStatement", True)

    def compile_expression(self) -> None:
        """Compiles an expression."""
        # Your code goes here!

        self.write_xml_tag("expression")
        self.compile_term()

        ops = []
        while self._input_stream.cur_token() in self.binary_op_dct_vm:
            ops.append(self._input_stream.cur_token())
            self._input_stream.advance()  # op
            self.compile_term()

        for op in ops:
            if op == '*':
                self.VMWriter.write_call('Math.multiply', 2)
            elif op == '/':
                self.VMWriter.write_call('Math.divide', 2)
            else:
                self.VMWriter.write_arithmetic(
                    self.binary_op_dct_vm[op])

        # while self._input_stream.cur_token() in self.binary_op_dct_vm:
        #     self.compile_term()
        #     if self._input_stream.cur_token() == '*':
        #         self.VMWriter.write_call('Math.multiply', 2)
        #     elif self._input_stream.cur_token() == '/':
        #         self.VMWriter.write_call('Math.divide', 2)
        #     else:
        #         self.VMWriter.write_arithmetic(
        #             self.binary_op_dct_vm[self._input_stream.cur_token()])
        #     self.write_token()  # op
        self.write_xml_tag("expression", True)

    def compile_term(self) -> None:
        """Compiles a term. 
        This routine is faced with a slight difficulty when
        trying to decide between some of the alternative parsing rules.
        Specifically, if the current token is an identifier, the routing must
        distinguish between a variable, an array entry, and a subroutine call.
        A single look-ahead token, which may be one of "[", "(", or "." suffices
        to distinguish between the three possibilities. Any other token is not
        part of this term and should not be advanced over.
        """
        # Your code goes here!
        self.write_xml_tag("term")
        if self._input_stream.token_type() == 'INT_CONST':
            self.VMWriter.write_push('CONST', self._input_stream.cur_token())
            self.write_token()  # the number

        if self._input_stream.token_type() == 'STRING_CONST':  # fixme: check
            string = self._input_stream.cur_token()
            # self.VMWriter.write_push('CONST', string) # line is wrong
            self.VMWriter.write_push('CONST', len(string))
            self.VMWriter.write_call('String.new', 1)
            for char in string:
                self.VMWriter.write_push('CONST', ord(char))
                self.VMWriter.write_call('String.appendChar', 2)
            self.write_token()  # the string

        elif self._input_stream.cur_token() in self.keyword_constant:
            self.VMWriter.write_push(
                self.keyword_constant_dct[self._input_stream.cur_token()][0],
                self.keyword_constant_dct[self._input_stream.cur_token()][1])
            if self._input_stream.cur_token() == 'true':
                self.VMWriter.write_arithmetic('NOT')
            self.write_token()  # the keywordConstant

        elif self._input_stream.cur_token() in self.unary_op_vm:
            op = self._input_stream.cur_token()
            self.write_token()  # ~ or -
            self.compile_term()
            self.VMWriter.write_arithmetic(self.unary_op_vm[op])

        elif self._input_stream.cur_token() == "(":
            self.write_token()  # (
            self.compile_expression()
            self.write_token()  # )

        elif self._input_stream.token_type() == "IDENTIFIER":
            identifier = self._input_stream.cur_token()
            self.write_token()  # identifier
            if self._input_stream.cur_token() == "[":  # fixme: check
                self.write_token()  # [
                self.compile_expression()
                self.write_token()  # ]
                # Compile array indexing
                kind = self.symbol_table.kind_of(identifier)
                index = self.symbol_table.index_of(identifier)
                self.VMWriter.write_push(CONVERT_KIND[kind], index)
                self.VMWriter.write_arithmetic('ADD')  # fixme change from '+'
                self.VMWriter.write_pop('POINTER', 1)
                self.VMWriter.write_push('THAT', 0)
            elif self._input_stream.cur_token() in {'.', '('}:
                self.compile_subroutine_call(
                    identifier)  # fixme: check if works
            else:
                var_kind = CONVERT_KIND[self.symbol_table.kind_of(identifier)]
                var_index = self.symbol_table.index_of(identifier)
                self.VMWriter.write_push(var_kind, var_index)

            # else:
            #     var = self._input_stream.cur_token()
            #     var_kind = CONVERT_KIND[self.symbol_table.kind_of(var)]
            #     var_index = self.symbol_table.index_of(var)
            #     self.VMWriter.write_push(var_kind, var_index)
            #
            # elif self._input_stream.cur_token() == "(":  # fixme: incomplited. should be expression list?
            #     self.write_token()  # (
            #     self.compile_expression()
            #     self.write_token()  # )
            # elif self._input_stream.cur_token() == ".":  # fixme:compileSubroutineCall(), like DoStatement
            #     self.write_token()  # '.' symbol
            #     identifier += '.' + self._input_stream.cur_token()
            #     self.write_token()  # subroutine name
            #     self.write_token()  # '(' symbol
            #     num_args = self.compile_expression_list()
            #     self.VMWriter.write_call(identifier, num_args)
            #     self.write_token()  # ')' symbol

        self.write_xml_tag("term", True)

    def compile_expression_list(
            self) -> int:
        """Compiles a (possibly empty) comma-separated list of expressions."""
        # Your code goes here!
        self.write_xml_tag("expressionList")
        num_args = 0
        if self._input_stream.cur_token() != ")":
            self.compile_expression()
            num_args += 1

        # fixme is a paramter list
        while self._input_stream.cur_token() == ",":
            self.write_token()  # ','
            self.compile_expression()
            num_args += 1

        self.write_xml_tag("expressionList", True)
        return num_args

    def write_token(self):
        type = self.type_dict[self._input_stream.token_type()]

        if self._input_stream.cur_token() in self.binary_op_dct_vm:
            t = self.binary_op_dct_vm[self._input_stream.cur_token()]
        else:
            t = self._input_stream.cur_token()

        token = f"#<{type}> {t} </{type}>\n"
        # self._output_stream.write(token)
        self._input_stream.advance()

    def compile_subroutine_call(self, identifier):
        num_args = 0
        if self._input_stream.cur_token() == '.':
            self.write_token()  # '.'
            sub_name = self._input_stream.cur_token()
            self.write_token()  # 'subname'
            if not self.symbol_table.type_of(identifier):
                func_name = f'{identifier}.{sub_name}'
            else:
                kind = self.symbol_table.kind_of(identifier)
                index = self.symbol_table.index_of(identifier)
                self.VMWriter.write_push(CONVERT_KIND[kind], index)
                func_name = f"{self.symbol_table.type_of(identifier)}.{sub_name}"
                num_args += 1

        else:  # method
            self.VMWriter.write_push("POINTER", 0)
            func_name = f"{self._class_name}.{identifier}"
            num_args += 1
        self.write_token()  # '('
        num_args += self.compile_expression_list()
        self.write_token()  # ')'
        self.VMWriter.write_call(func_name, num_args)

    def write_xml_tag(self, tag, end=False):
        return
        self._output_stream.write(f"<{'/' if end else ''}{tag}>\n")
