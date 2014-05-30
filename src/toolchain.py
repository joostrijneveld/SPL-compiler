#! /usr/bin/env python

# from __future__ import print_function
import sys
import io

import scanner
import parser
import prettyprinter
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
	fin = io.open(sys.argv[1], encoding='utf-8')
	# with open(sys.argv[1], 'r') as fin:
	tokens = scanner.scan_spl(fin)
	fin.close()
	print map(unicode, tokens)

	# print len(tokens)
	# tree = parser.build_tree(tokens)
	# print str(tree)
	# predefined = {
	# 	'isEmpty': Symbol(0, 0, Type('Bool'), [Type([Type('t')])], True, None),
	# 	'print'  : Symbol(0, 0, Type('Void'), [Type('t')], True, None)
	# }
	# symtab = semanticanalysis.check_binding(tree, predefined)
	# prettyprinter.print_tree(tree)
	# with open(sys.argv[2], 'w') as fout:
	# 	generator.generate_ssm(tree, symtab, fout)
	
if __name__ == '__main__':
	main()
