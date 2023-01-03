"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import re
import typing

KEYORDS = {'class', 'constructor', 'function', 'method', 'field',
           'static', 'var', 'int', 'char', 'boolean', 'void', 'true',
           'false', 'null', 'this', 'let', 'do', 'if', 'else',
           'while', 'return'}
SYMBOLS = {'{', '}', '(', ')', '[', ']', '.', ',', ';', '+', '|', '&'
    , '-', '*', '/', '&', ',', '<', '>', '=', '~', '^', '#'}


def find_quoted_substrings(s: str):
    """"
    to handle with comment in string s.t: "hi // this is not a comment"
    """
    start_index = None
    quote_char = None

    num_of_string = 0
    dct = {}

    for i, c in enumerate(s):
        if c == '"' or c == "'":
            if start_index is None:
                # start of a quoted substring
                start_index = i
                quote_char = c
            elif quote_char == c:
                # end of a quoted substring

                tmp_id = f"STR{num_of_string}"
                dct[tmp_id] = s[start_index:i + 1]

                num_of_string += 1

                start_index = None
                quote_char = None

    for key, val in dct.items():
        s = s.replace(val, key)

    return s, dct


def r(input_string):
    # input_string = re.sub(r'/\*.*?\*/', '', input_string, flags=re.DOTALL)
    # # Replace /** API comment until closing */ with an empty string
    # input_string = re.sub(r'/\*\*.*?\*/', '', input_string, flags=re.DOTALL)
    # # Replace // comment until the line's end with an empty string
    # input_string = re.sub(r'//.*', '', input_string)
    #
    input_string = re.sub(r'//[^\n]*\n|/\*(.*?)\*/','', input_string, flags=re.DOTALL)

    return input_string


def remove_comments(jack_file):
    # We will use a regular expression to match the three possible comment formats

    # jack_file, dct = find_quoted_substrings(jack_file)
    # regex = r"(//.*)|(/\*([^*]|[\r\n]|(\*+([^*/]|[\r\n])))*\*+/)"
    #
    # # Replace all matches with an empty string
    # jack_file = re.sub(regex, "", jack_file)

    jack_file = r(jack_file)

    out_list = re.findall(
        r"[\w]+|[*\{\}()\[\].,;+\\\-&/|<>=~\?]|[\"\'].+[\"\']", jack_file)

    # for i in range(len(out_list)):
    #     if out_list[i] in dct:
    #         out_list[i] = dct[out_list[i]]

    return out_list


class JackTokenizer:
    """Removes all comments from the input stream and breaks it
    into Jack language tokens, as specified by the Jack grammar.
    
    # Jack Language Grammar

    A Jack file is a stream of characters. If the file represents a
    valid program, it can be tokenized into a stream of valid tokens. The
    tokens may be separated by an arbitrary number of whitespace characters, 
    and comments, which are ignored. There are three possible comment formats: 
    /* comment until closing */ , /** API comment until closing */ , and 
    // comment until the line’s end.

    - ‘xxx’: quotes are used for tokens that appear verbatim (‘terminals’).
    - xxx: regular typeface is used for names of language constructs 
           (‘non-terminals’).
    - (): parentheses are used for grouping of language constructs.
    - x | y: indicates that either x or y can appear.
    - x?: indicates that x appears 0 or 1 times.
    - x*: indicates that x appears 0 or more times.

    ## Lexical Elements

    The Jack language includes five types of terminal elements (tokens).

    - keyword: 'class' | 'constructor' | 'function' | 'method' | 'field' | 
               'static' | 'var' | 'int' | 'char' | 'boolean' | 'void' | 'true' |
               'false' | 'null' | 'this' | 'let' | 'do' | 'if' | 'else' | 
               'while' | 'return'
    - symbol: '{' | '}' | '(' | ')' | '[' | ']' | '.' | ',' | ';' | '+' | 
              '-' | '*' | '/' | '&' | '|' | '<' | '>' | '=' | '~' | '^' | '#'
    - integerConstant: A decimal number in the range 0-32767.
    - StringConstant: '"' A sequence of Unicode characters not including 
                      double quote or newline '"'
    - identifier: A sequence of letters, digits, and underscore ('_') not 
                  starting with a digit. You can assume keywords cannot be
                  identifiers, so 'self' cannot be an identifier, etc'.

    ## Program Structure

    A Jack program is a collection of classes, each appearing in a separate 
    file. A compilation unit is a single class. A class is a sequence of tokens 
    structured according to the following context free syntax:
    
    - class: 'class' className '{' classVarDec* subroutineDec* '}'
    - classVarDec: ('static' | 'field') type varName (',' varName)* ';'
    - type: 'int' | 'char' | 'boolean' | className
    - subroutineDec: ('constructor' | 'function' | 'method') ('void' | type) 
    - subroutineName '(' parameterList ')' subroutineBody
    - parameterList: ((type varName) (',' type varName)*)?
    - subroutineBody: '{' varDec* statements '}'
    - varDec: 'var' type varName (',' varName)* ';'
    - className: identifier
    - subroutineName: identifier
    - varName: identifier

    ## Statements

    - statements: statement*
    - statement: letStatement | ifStatement | whileStatement | doStatement | 
                 returnStatement
    - letStatement: 'let' varName ('[' expression ']')? '=' expression ';'
    - ifStatement: 'if' '(' expression ')' '{' statements '}' ('else' '{' 
                   statements '}')?
    - whileStatement: 'while' '(' 'expression' ')' '{' statements '}'
    - doStatement: 'do' subroutineCall ';'
    - returnStatement: 'return' expression? ';'

    ## Expressions
    
    - expression: term (op term)*
    - term: integerConstant | stringConstant | keywordConstant | varName | 
            varName '['expression']' | subroutineCall | '(' expression ')' | 
            unaryOp term
    - subroutineCall: subroutineName '(' expressionList ')' | (className | 
                      varName) '.' subroutineName '(' expressionList ')'
    - expressionList: (expression (',' expression)* )?
    - op: '+' | '-' | '*' | '/' | '&' | '|' | '<' | '>' | '='
    - unaryOp: '-' | '~' | '^' | '#'
    - keywordConstant: 'true' | 'false' | 'null' | 'this'
    
    Note that ^, # correspond to shiftleft and shiftright, respectively.
    """

    def __init__(self, input_stream: typing.TextIO) -> None:
        """Opens the input stream and gets ready to tokenize it.

        Args:
            input_stream (typing.TextIO): input stream.
        """
        # Your code goes here!
        # A good place to start is to read all the lines of the input:
        # input_lines = input_stream.read().splitlines()

        self.cur = 0
        self._input_lines = remove_comments(input_stream.read())
        self.dct_token_type = {"KEYWORD",
                               "SYMBOL",
                               "IDENTIFIER",
                               "INT_CONST",
                               "STRING_CONST"}

    def has_more_tokens(self) -> bool:
        """Do we have more tokens in the input?

        Returns:
            bool: True if there are more tokens, False otherwise.
        """
        return self.cur < len(self._input_lines)

    def advance(self) -> None:
        """Gets the next token from the input and makes it the current token. 
        This method should be called if has_more_tokens() is true. 
        Initially there is no current token.
        """
        # Your code goes here!
        self.cur += 1

    def token_type(self) -> str:
        """
        Returns:
            str: the type of the current token, can be
            "KEYWORD", "SYMBOL", "IDENTIFIER", "INT_CONST", "STRING_CONST"
        """
        # Your code goes here!
        cur_token = self._input_lines[self.cur]
        if cur_token in KEYORDS:
            return "KEYWORD"
        elif cur_token in SYMBOLS:
            return "SYMBOL"
        elif all(c.isdigit() for c in cur_token):
            return "INT_CONST"
        if (cur_token.startswith("'") and cur_token.endswith("'")) or (
                cur_token.startswith('"') and cur_token.endswith('"')):
            return "STRING_CONST"
        else:
            return "IDENTIFIER"

    def keyword(self) -> str:
        """
        Returns:
            str: the keyword which is the current token.
            Should be called only when token_type() is "KEYWORD".
            Can return "CLASS", "METHOD", "FUNCTION", "CONSTRUCTOR", "INT", 
            "BOOLEAN", "CHAR", "VOID", "VAR", "STATIC", "FIELD", "LET", "DO", 
            "IF", "ELSE", "WHILE", "RETURN", "TRUE", "FALSE", "NULL", "THIS"
        """
        # Your code goes here!
        return self._input_lines[self.cur].upper()

    def symbol(self) -> str:
        """
        Returns:
            str: the character which is the current token.
            Should be called only when token_type() is "SYMBOL".
            Recall that symbol was defined in the grammar like so:
            symbol: '{' | '}' | '(' | ')' | '[' | ']' | '.' | ',' | ';' | '+' | 
              '-' | '*' | '/' | '&' | '|' | '<' | '>' | '=' | '~' | '^' | '#'
        """
        # Your code goes here!
        return self._input_lines[self.cur]

    def identifier(self) -> str:
        """
        Returns:
            str: the identifier which is the current token.
            Should be called only when token_type() is "IDENTIFIER".
            Recall that identifiers were defined in the grammar like so:
            identifier: A sequence of letters, digits, and underscore ('_') not 
                  starting with a digit. You can assume keywords cannot be
                  identifiers, so 'self' cannot be an identifier, etc'.
        """
        # Your code goes here!
        return self._input_lines[self.cur]

    def int_val(self) -> int:
        """
        Returns:
            str: the integer value of the current token.
            Should be called only when token_type() is "INT_CONST".
            Recall that integerConstant was defined in the grammar like so:
            integerConstant: A decimal number in the range 0-32767.
        """
        # Your code goes here!
        return int(self._input_lines[self.cur])

    def string_val(self) -> str:
        """
        Returns:
            str: the string value of the current token, without the double 
            quotes. Should be called only when token_type() is "STRING_CONST".
            Recall that StringConstant was defined in the grammar like so:
            StringConstant: '"' A sequence of Unicode characters not including 
                      double quote or newline '"'
        """
        # Your code goes here!
        return self._input_lines[self.cur].replace("\n", "")[1:-1]

    def cur_token(self):
        if self.token_type() == "KEYWORD":
            return self.keyword().lower()
        if self.token_type() == "SYMBOL":
            return self.symbol()
        if self.token_type() == "IDENTIFIER":
            return self.identifier()
        if self.token_type() == "INT_CONST":
            return self.int_val()
        if self.token_type() == "STRING_CONST":
            return self.string_val()
