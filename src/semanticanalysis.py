#! /usr/bin/env python

import collections
import sys
from functools import partial

Symbol = collections.namedtuple('Symbol', ['line','col','type','argtype'])

class Type:
	def __init__(self, value):
		self.value = value
	
	@staticmethod
	def from_node(tree):
		if tree.tok.type in ['Bool', 'Int']:
			return Type(tree.tok.type)
		elif tree.tok.type == 'id':
			return Type(tree.tok.val)
		elif tree.tok.type == ',':
			return (Type.from_node(tree.children[0]), Type.from_node(tree.children[1]))
		elif tree.tok.type == '[':
			return [Type.from_node(tree.children[0])]

	def __repr__(self):
		return self.value
		
	def __eq__(self, other):
		return self.value == other.value
		
def print_symboltable(symboltable):
	print '='*62
	print ("{0: <12} {1: <15} {2: <15} {3: <20}"
			.format('Position', 'Name', 'Type', 'Argtypes'))
	print '-'*62
	for k, v in symboltable.iteritems():
		argvstring =  ", ".join(map(str,v.argtype)) if v.argtype else None
		print ("{: <12} {: <15} {: <15} {: <20}"
				.format("{0.line}:{0.col}".format(v), k, v.type, argvstring))
	print '='*62

def find_argtypes(tree):
	''' expects a tree with an arg-node (',') as root '''
	if not tree:
		return []
	return [Type.from_node(tree.children[0])] + find_argtypes(tree.children[2])

def update_symbols(symbols, sym, t, argtypes):
	if sym.val in symbols:
		dupsym = symbols[sym.val]
		raise Exception("[Line {}:{}] Redefinition of {}\n"+
						"[Line {}:{}] Previous definition was here"
						.format(dupsym.line, dupsym.col, sym.val,
								sym.line, sym.col))
	symbols.update({sym.val : Symbol(sym.line, sym.col, t, argtypes)})
	return symbols

def create_table(tree):
	''' expects a tree with a Decl-node as root '''
	if not tree:
		return dict()
	t = Type.from_node(tree.children[0].children[0])
	sym = tree.children[0].children[1].tok
	argtypes = None  # VarDecls do not have arguments
	if tree.children[0].tok == 'FunDecl':
		argtypes = find_argtypes(tree.children[0].children[2])
	symbols = create_table(tree.children[1])
	return update_symbols(symbols, sym, t, argtypes)

def create_argtable(tree):
	''' expects a tree with an arg-node (',') as root '''
	if not tree:
		return dict()
	t = Type.from_node(tree.children[0])
	sym = tree.children[1].tok
	symbols = create_argtable(tree.children[2])
	return update_symbols(symbols, sym, t, None)

def create_functiontable(tree):
	argsymboltable = create_argtable(tree.children[2])
	localsymboltable = create_table(tree.children[3])
	for key in set(localsymboltable.keys()) & set(argsymboltable.keys()):
		dupsym = symbols[key]
		raise Exception("[Line {}:{}] Redefinition of {}\n"+
						"[Line {}:{}] Previous definition was here"
						.format(dupsym.line, dupsym.col, sym.val,
								sym.line, sym.col))
	localsymboltable.update(argsymboltable)
	return localsymboltable

def type_op2(fn, tree, symtab, expected_type):
	if tree.tok.type == '||':
		t1, t2 = map(type_exp, *tree.children[0])
		if t1 != expected_type or t2 != expected_type:
			raise Exception("[Line {}:{}] Incompatible types for operator {}\n"
							+ "Types found: {} {}"
							.format(tree.tok.line, tree.tok.col, tree.tok.type,
								t1, t2))
		return expected_type
	return fn(tree, symtab)

type_exp_and = id
type_exp_or = partial(type_op2, type_exp_and, expected_type='Bool')
type_exp = type_exp_or

def type_expargs(tree, symtab):
	''' expects a tree with an arg-node (',') as root '''
	if not tree:
		return []
	return ([type_exp(tree.children[0], symtab)]
			+ type_expargs(tree.children[1].symtab))

def type_expfunc(tree, symtab):
	return symtab[tree.children[0].tok.val].type

def check_stmt(tree, symboltable):	
	''' expects a tree with a statement node as root '''
	return
	print tree
	if tree.tok == 'Scope':
		check_stmts(tree.children[0], symboltable)
	elif tree.tok == 'FunCall':
		out(tree.children[0].tok.val, depth)
		out('(')
		if tree.children[1]:
			print_act_args(tree.children[1])
		out(');\n')
	elif tree.tok.type == 'if':
		out('if (', depth)
		print_exp(tree.children[0])
		out(')\n')
		print_stmt(tree.children[1], depth + int(tree.children[1].tok != 'Scope'))
		if tree.children[2]:
			out('else\n', depth)
			print_stmt(tree.children[2], depth + int(tree.children[2].tok != 'Scope'))
	elif tree.tok.type == 'while':
		out('while (', depth)
		print_exp(tree.children[0])
		out(')\n')
		print_stmt(tree.children[1], depth + int(tree.children[1].tok != 'Scope'))
	elif tree.tok.type == '=':
		out('', depth)
		print_field(tree.children[0])
		out(' = ')
		print_exp(tree.children[1])
		out(';\n')
	elif tree.tok.type == 'return':
		out('return', depth)
		if tree.children[0]:
			out(' ')
			print_exp(tree.children[0])
		out(';\n')
	
def check_stmts(tree, symboltable):
	if tree:
		check_stmt(tree.children[0], symboltable)
		check_stmts(tree.children[1], symboltable)

def check_functionbinding(tree, globalsymboltable):
	functionsymboltable = create_functiontable(tree)
	for key in set(functionsymboltable.keys()) & set(globalsymboltable.keys()):
		dupsym = symbols[key]
		sys.stderr.write("[Line {}:{}] Warning: redefinition of global {}\n"+
						"[Line {}:{}] Previous definition was here"
						.format(dupsym.line, dupsym.col, sym.val,
								sym.line, sym.col))
	symboltable = globalsymboltable.copy().update(functionsymboltable)
	check_stmts(tree.children[4], symboltable)

def check_localbinding(tree, globalsymboltable):
	if not tree:
		return
	if tree.children[0].tok == 'FunDecl':
		check_functionbinding(tree.children[0], globalsymboltable)
	check_localbinding(tree.children[1], globalsymboltable)

def check_binding(tree):
	globalsymboltable = create_table(tree)
	print_symboltable(globalsymboltable)
	check_localbinding(tree, globalsymboltable)
	
