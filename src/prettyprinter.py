#! /usr/bin/env python

from sys import stdout
out = stdout.write

def print_exp(tree):
	if tree.val[0] == 'int':
		out(str(tree.val[1]))
	elif tree.val[0] == 'id':
		out(tree.val[1])
	elif tree.val in ['True', 'False']:
		out(tree.val)
	elif tree.val in ['!', '-']:
		out(tree.val)
		print_exp(tree.children[0])
	elif tree.val in ['+', '*', '/', '%', ':', '&&', '||', '==', '<', '>', '<=', '>=', '!=']:
		out('(')
		print_exp(tree.children[0])
		out(tree.val)
		print_exp(tree.children[1])
		out(')')
	elif tree.val == ',':
		out('(')
		print_exp(tree.children[0])
		out(tree.val)
		print_exp(tree.children[1])
		out(')')
	
def print_tree(tree):
	print_exp(tree)