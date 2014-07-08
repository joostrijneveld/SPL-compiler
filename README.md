## Simple Programming Language compiler

**Usage:** `python3 src/toolchain.py [-h] [-vvvv] inputfile.spl outputfile.ssm`

This repository contains our SPL compiler. Note that our project relies on a different SSM interpreter than included by default, so as to allow us to implement user interaction and file IO in our SPL dialect. The fork that produced this version of the interpreter can be found [here](https://github.com/joostrijneveld/ssm).

Among other things, this repository contains the following files:

**src/toolchain.py** The toolchain calls the scanner, parser, printer, type checker and code generator consecutively, passing the result from one on to the next. This is the script you need to execute to parse, print, type check and finally generate a .ssm file from a .spl source file.<br>
**src/scanner.py** This file contains the scanner. The scanner expects a filename and produces a list of Tokens that can then be passed on to the parser. `Token` objects contain a position (line / col) to indicate where the token was found, for future error handling.<br>
**src/parser.py** The parser expects a list of `Token` objects, as produced by the scanner. It then outputs the root of a parse tree (a `Node` object). Grammar rules can be mapped one-to-one to `parse_` functions, some of which are generated based on a blueprint function that is partially applied (the `tail_recursion` function). When the parser runs into an error, it prints the expected literal (if applicable) and the line and column number.<br>
**src/semanticanalysis.py** This is the type and function binding checker. It will check for type errors and function binding errors, when it is called with the `check_binding` function. It expects a tree that can be generated using the parser. A dictionary with a symbol table of predefined functions can be passed as an optional argument. The `Symbol` class is also defined in this file.<br>
**src/printer.py** This script expects a parse tree as provided by the parser, and prints formatted (and aligned) SPL source code to stdout.<br>
**src/generator.py** This script expects a type checked parse tree as provided by the type checker, and write generated SSM machine code to the given filename.<br>
**src/stdlib.py** This file contains a dictionary of built-in SPL functions with their function signature and SSM assembly implementations. This is especially relevant for file IO. <br>
**spl/*** This folder contains sample SPL programs. All of them parse, print, type check and generate code just fine. Some of them have wrong statements (with type errors) in comments, which can be enabled to trigger type check errors. In the report, we explain these programs and their result in more details.<br>
**grammar.txt** This file contains the modified grammar which we used for our compiler.<br>
