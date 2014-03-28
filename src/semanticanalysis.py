#! /usr/bin/env python

import collections

Symbol = collections.namedtuple('Symbol', ['line','col','type','argtype'])

def print_symboltable(symboltable):
	print 'Position\tName\t\tType\tArgtypes'
	print '-'*50
	for k, v in symboltable.iteritems():
		if v.argtype:
			argvstring =  ", ".join(str(t) for t in v.argtype)
		else:
			argvstring = "None"
		print ("[Line {}:{}]\t{}\t\t{}\t{}"
				.format(v.line, v.col, k, v.type, argvstring))

def find_argtypes(tree):
	""" expects a tree with an arg-node (',') as root """
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
	""" expects a tree with an arg-node (',') as root """
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
	
