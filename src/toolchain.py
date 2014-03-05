#! /usr/bin/env python

import sys
import parser, scanner

def main():
	tokens = scanner.scan_spl(sys.argv[1])
	print tokens
	print parser.build_tree(tokens)
	
if __name__ == '__main__':
	main()