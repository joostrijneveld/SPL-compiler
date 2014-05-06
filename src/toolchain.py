#! /usr/bin/env python

# from __future__ import print_function
import sys
import parser, scanner, prettyprinter
import semanticanalysis
import generator
from semanticanalysis import Type, Symbol

def help():
	print("Usage: toolchain.py inputfile.spl outputfile.ssm")

def main():
	# sys.tracebacklimit = 0 # so that we only show our own exceptions
	sys.setrecursionlimit(10000) # since were compiling recursively..
	if len(sys.argv) != 3:
		help()
		return
		
	with open(sys.argv[1], 'r') as fin:
		tokens = scanner.scan_spl(fin)
	tree = parser.build_tree(tokens)
	print str(tree)
	# prettyprinter.print_tree(tree)
	predefined = {
		'isEmpty': Symbol(0, 0, Type('Bool'), [Type([Type('t')])], True, None),
		'print'  : Symbol(0, 0, Type('Void'), [Type('t')], True, None)
	}
	symtabs = semanticanalysis.check_binding(tree, predefined)
	with open(sys.argv[2], 'w') as fout:
		generator.generate_ssm(tree, symtabs, fout)
	
if __name__ == '__main__':
	main()
