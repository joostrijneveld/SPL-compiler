#! /usr/bin/env python

import sys
import io
import argparse

import scanner
import parser
import prettyprinter
import semanticanalysis
import generator
import stdlib

from semanticanalysis import Type, Symbol


def main():
    argparser = argparse.ArgumentParser(
        description='Compiles SPL programs toSSM instruction files.')
    argparser.add_argument('spl', metavar='infile',
        help="the SPL source file")
    argparser.add_argument('ssm', metavar='outfile',
        help="the SSM output file")
    argparser.add_argument('--verbose', '-v', action='count',
        help="increase the level of verbosity")
    args = argparser.parse_args()
    if not args.verbose or args.verbose < 4:
        sys.tracebacklimit = 0  # so that we only show our own exceptions
    sys.setrecursionlimit(10000)  # since we're compiling recursively..
    with io.open(args.spl, encoding='utf-8') as fin:
        tokens = scanner.scan_spl(fin)
    tree = parser.build_tree(tokens)
    usedsyms, symtabs = semanticanalysis.check_binding(tree, stdlib.functions)
    with open(args.ssm, 'w') as fout:
        generator.generate_ssm(tree, usedsyms, stdlib.functions, fout)
    if args.verbose:
        if args.verbose >= 2:
            prettyprinter.print_tree(tree)
        if args.verbose >= 3:
            print(tree)
        semanticanalysis.print_symboltables(symtabs)
    print("Successfully compiled {0.spl} to {0.ssm}.".format(args))

if __name__ == '__main__':
    main()
