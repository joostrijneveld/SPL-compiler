#! /usr/bin/env python

# from __future__ import print_function
import sys
import parser, scanner, prettyprinter
import semanticanalysis

def help():
	print("Usage: toolchain.py inputfile.spl")

def main(): 
	if len(sys.argv) != 2:
		help()
		return
	tokens = scanner.scan_spl(sys.argv[1])
	tree = parser.build_tree(tokens)
	print str(tree)
	prettyprinter.print_tree(tree)
	semanticanalysis.check_binding(tree)
	
if __name__ == '__main__':
	main()
