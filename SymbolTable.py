"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import typing

TYPE = 0
KIND = 1
INDEX = 2

class SymbolTable:
    """A symbol table that associates names with information needed for Jack
    compilation: type, kind and running index. The symbol table has two nested
    scopes (class/subroutine).
    """

    def __init__(self) -> None:
        """Creates a new empty symbol table."""
        # Your code goes here!
        self._class_scope = {}
        self._subroutine_scope = {}
        self._counter = {"STATIC": 0, "FIELD": 0, "ARG": 0, "VAR": 0}
        self._in_class_scope = True


    def start_subroutine(self) -> None:
        """Starts a new subroutine scope (i.e., resets the subroutine's 
        symbol table).
        """
        # Your code goes here!
        self._subroutine_scope = {}
        self._counter["ARG"] = 0
        self._counter["VAR"] = 0
        self._in_class_scope = False

    def define(self, name: str, type: str, kind: str) -> None:
        """Defines a new identifier of a given name, type and kind and assigns 
        it a running index. "STATIC" and "FIELD" identifiers have a class scope, 
        while "ARG" and "VAR" identifiers have a subroutine scope.

        Args:
            name (str): the name of the new identifier.
            type (str): the type of the new identifier.
            kind (str): the kind of the new identifier, can be:
            "STATIC", "FIELD", "ARG", "VAR".
        """
        # Your code goes here!
        if kind in ["STATIC", "FIELD"]:
            self._class_scope[name] = [type, kind, self._counter[kind]]
            self._counter[kind] += 1
        elif kind in ["ARG", "VAR"]:
            self._subroutine_scope[name] = [type, kind, self._counter[kind]]
            self._counter[kind] += 1

    def var_count(self, kind: str) -> int:
        """
        Args:
            kind (str): can be "STATIC", "FIELD", "ARG", "VAR".

        Returns:
            int: the number of variables of the given kind already defined in 
            the current scope.
        """
        # Your code goes here!
        return self._counter[kind]

    def kind_of(self, name: str) -> str:
        """
        Args:
            name (str): name of an identifier.

        Returns:
            str: the kind of the named identifier in the current scope, or None
            if the identifier is unknown in the current scope.
        """

        return self.helper(name, KIND)


    def type_of(self, name: str) -> str:
        """
        Args:
            name (str):  name of an identifier.

        Returns:
            str: the type of the named identifier in the current scope.
        """
        # Your code goes here!
        return self.helper(name, TYPE)

    def index_of(self, name: str) -> int:
        """
        Args:
            name (str):  name of an identifier.

        Returns:
            int: the index assigned to the named identifier.
        """

        return self.helper(name, INDEX)

    def helper(self, name, request):
        out = None

        if name in self._class_scope:
            out = self._class_scope[name][request]

        if not self._in_class_scope:
            if name in self._subroutine_scope:
                out = self._subroutine_scope[name][request]

        return out

