#! /usr/bin/env python

from collections import deque
import sys
import parser, scanner, prettyprinter

def main():
	tokens = scanner.scan_spl(sys.argv[1])
	tree = parser.build_tree(deque(tokens))
	print tokens
	print tree
	prettyprinter.print_tree(tree)
	
if __name__ == '__main__':
	main()