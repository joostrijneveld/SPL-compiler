#! /usr/bin/env python

import sys
import parser, scanner, prettyprinter

def help():
        print "Usage: toolchain.py inputfile.spl"

def main(): 
	if len(sys.argv) != 2:
		help()
		return
	tokens = scanner.scan_spl(sys.argv[1])
	tree = parser.build_tree(tokens)
	prettyprinter.print_tree(tree)
	
if __name__ == '__main__':
	main()
