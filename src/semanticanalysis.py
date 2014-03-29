#! /usr/bin/env python

import collections

Symbol = collections.namedtuple('Symbol', ['line','col','type','argtype'])

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
	return [tree.children[0]] + find_argtypes(tree.children[2])

def create_table(tree):
	if not tree:
		return dict()
	t = tree.children[0].children[0]
	sym = tree.children[0].children[1].tok
	argtypes = None  # VarDecls do not have arguments
	if tree.children[0].tok == 'FunDecl':
		argtypes = find_argtypes(tree.children[0].children[2])
	symbols = create_table(tree.children[1])
	if sym.val in symbols:
		dupsym = symbols[sym.val]
		raise Exception("[Line {}:{}] Redefinition of {}\n"+
						"[Line {}:{}] Previous definition was here"
						.format(dupsym.line, dupsym.col, sym.val,
								sym.line, sym.col))
	symbols.update({sym.val : Symbol(sym.line, sym.col, t, argtypes)})
	return symbols

def create_argtable(tree):
	''' expects a tree with an arg-node (',') as root '''
	if not tree:
		return dict()
	t = tree.children[0]
	sym = tree.children[1].tok
	symbols = create_argtable(tree.children[2])
	argtypes = None  # VarDecls do not have arguments
	if sym.val in symbols:
		dupsym = symbols[sym.val]
		raise Exception("[Line {}:{}] Redefinition of {}\n"+
						"[Line {}:{}] Previous definition was here"
						.format(dupsym.line, dupsym.col, sym.val,
								sym.line, sym.col))
	symbols.update({sym.val : Symbol(sym.line, sym.col, t, argtypes)})
	return symbols

def check_functionbinding(tree, symboltable):
	argsymboltable = create_argtable(tree.children[2])
	localsymboltable = create_table(tree.children[3])
	for key in set(localsymboltable.keys()) & set(argsymboltable.keys()):
		dupsym = symbols[key]
		raise Exception("[Line {}:{}] Redefinition of {}\n"+
						"[Line {}:{}] Previous definition was here"
						.format(dupsym.line, dupsym.col, sym.val,
								sym.line, sym.col))
	localsymboltable.update(argsymboltable)
	print_symboltable(localsymboltable)
	# TODO: check binding

def check_localbinding(tree, symboltable):
	if not tree:
		return
	if tree.children[0].tok == 'FunDecl':
		check_functionbinding(tree.children[0], symboltable)
	check_localbinding(tree.children[1], symboltable)

def check_binding(tree):
	globalsymboltable = create_table(tree)
	print_symboltable(globalsymboltable)
	check_localbinding(tree, globalsymboltable)
	
