#! /usr/bin/env python

from sys import stdout
from functools import partial

def out(s, tabs=0):
	stdout.write('\t'*tabs + s)

def print_decl(tree, depth=0):
	if tree.val == 'VarDecl':
		print_vardecl(tree)
	else:
		print_fundecl(tree)

def print_vardecl(tree, depth=0):
	out('', depth)
	print_type(tree.children[0])
	out(' '+tree.children[1].val[1]+' = ')
	print_exp(tree.children[2])
	out(';\n')
	
def print_fundecl(tree):
	print_rettype(tree.children[0])
	out(' '+tree.children[1].val[1]+'(')
	if tree.children[2]:
		print_fargs(tree.children[2])
	out(')\n{\n')
	if tree.children[3]:
		print_vardecl_list(tree.children[3], 1)
	print_stmt_list(tree.children[4], 1)
	out('}\n')
	
def print_fargs(tree):
	print_type(tree.children[0])
	out(' '+tree.children[1].val[1])
	if tree.children[2]:
		out(', ')
		print_fargs(tree.children[2])
	
def print_rettype(tree):
	if tree.val == 'Void':
		out('Void')
	else:
		print_type(tree)
		
def print_type(tree):
	if tree.val in ['Int', 'Bool']:
		out(tree.val)
	elif type(tree.val) is tuple and tree.val[0] == 'id':
		out(tree.val[1])
	elif tree.val == ',':
		out('(')
		print_type(tree.children[0])
		out(',')
		print_type(tree.children[1])
		out(')')
	elif tree.val == '[]':
		out('[')
		print_type(tree.children[0])
		out(']')
		
def print_stmt(tree, depth):
	if tree.val == '{}':
		out('{\n', depth)
		if tree.children[0]:
			print_stmt_list(tree.children[0], depth+1)
		out('}\n', depth)
	elif tree.val == 'if':
		out('if (', depth)
		print_exp(tree.children[0])
		out(')\n')
		print_stmt(tree.children[1], depth + int(tree.children[1].val != '{}'))
		if tree.children[2]:
			out('else\n', depth)
			print_stmt(tree.children[2], depth + int(tree.children[1].val != '{}'))
	elif tree.val == 'while':
		out('while (', depth)
		print_exp(tree.children[0])
		out(')\n')
		print_stmt(tree.children[1], depth + int(tree.children[1].val != '{}'))
	elif tree.val == '=':
		out('', depth)
		print_field(tree.children[0])
		out(' = ')
		print_exp(tree.children[1])
		out(';\n')
	elif tree.val == 'FunCall':
		out(tree.children[0].val[1], depth)
		out('(')
		if tree.children[1]:
			print_act_args(tree.children[1])
		out(');\n')
	elif tree.val == 'return':
		out('return', depth)
		if tree.children[0]:
			out(' ')
			print_exp(tree.children[0])
		out(';\n')
		
def print_exp(tree):
	if tree.val in ['!', '-'] and len(tree.children) == 1:
		out(tree.val)
		print_exp(tree.children[0])
	elif tree.val in ['-', '+', '*', '/', '%', ':',
					  '&&', '||', '==', '<', '>', '<=', '>=', '!=']:
		out('(')
		print_exp(tree.children[0])
		out(' '+tree.val+' ')
		print_exp(tree.children[1])
		out(')')
	elif tree.val[0] == 'int':
		out(str(tree.val[1]))
	elif tree.val[0] == 'bool':
		out(str(tree.val[1]))
	elif tree.val == 'FunCall':
		out(tree.children[0].val[1])
		out('(')
		if tree.children[1]:
			print_act_args(tree.children[1])
		out(')')
	elif tree.val in ['.hd', '.tl', '.fst', '.snd'] \
		or type(tree.val) is tuple and tree.val[0] == 'id':
		print_field(tree)
	elif tree.val == '[]':
		out('[]')
	elif tree.val == ',':
		out('(')
		print_exp(tree.children[0])
		out(', ')
		print_exp(tree.children[1])
		out(')')

def print_field(tree):
	if type(tree.val) is tuple and tree.val[0] == 'id':
		out(tree.val[1])
	else:
		print_field(tree.children[0])
		out(tree.val)

def print_act_args(tree):
	print_exp(tree.children[0])
	if tree.children[1]:
		out(', ')
		print_act_args(tree.children[1])

def nonterminal_list(fn, tree, depth):
	fn(tree.children[0], depth)
	if tree.children[1]:
		nonterminal_list(fn, tree.children[1], depth)

print_decl_list = partial(nonterminal_list, print_decl)
print_vardecl_list = partial(nonterminal_list, print_vardecl)
print_stmt_list = partial(nonterminal_list, print_stmt)

def print_tree(tree):
	print_decl_list(tree, 0)
	out('\n')