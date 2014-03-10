#! /usr/bin/env python

import sys
import parser, scanner, prettyprinter

def main():
	tokens = scanner.scan_spl(sys.argv[1])
	tree = parser.build_tree(tokens)
	print tree
	prettyprinter.print_tree(tree)
	
if __name__ == '__main__':
	main()
