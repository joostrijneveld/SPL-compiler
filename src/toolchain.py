#! /usr/bin/env python

# from __future__ import print_function
import sys
import parser, scanner, prettyprinter
import semanticanalysis
from semanticanalysis import Type, Symbol

def help():
	print("Usage: toolchain.py inputfile.spl")

def main():
	# sys.tracebacklimit = 0 # so that we only show our own exceptions
	sys.setrecursionlimit(10000) # since were compiling recursively..
	if len(sys.argv) != 2:
		help()
		return
	tokens = scanner.scan_spl(sys.argv[1])
	tree = parser.build_tree(tokens)
	# print str(tree)
	# prettyprinter.print_tree(tree)
	predefined = {
		'isEmpty' 	: Symbol(0, 0, Type('Bool'), [Type([Type('t')])], True),
		'print' 	: Symbol(0, 0, Type('Void'), [Type('t')], True)
		}
	semanticanalysis.check_binding(tree, predefined)
	
if __name__ == '__main__':
	main()
