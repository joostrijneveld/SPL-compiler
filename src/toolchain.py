#! /usr/bin/env python

import parser, scanner

def main():
	tokens = scanner.scan_spl('../test.spl')
	parser.build_tree(tokens)
	
if __name__ == '__main__':
	main()