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
		if tree.tok.type in ['Bool', 'Int', 'Void']:
			return Type(tree.tok.type)
		elif tree.tok.type == 'id':
			return Type(tree.tok.val)
		elif tree.tok.type == ',':
			return (Type.from_node(tree.children[0]),
					Type.from_node(tree.children[1]))
		elif tree.tok.type == '[':
			return [Type.from_node(tree.children[0])]

	def __repr__(self):
		return self.value
		
	def __eq__(self, other):
		return self.value == other.value
		
	def __ne__(self, other):
		return self.value != other.value
		
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
		raise Exception("[Line {}:{}] Redefinition of {}\n"
						"[Line {}:{}] Previous definition was here"
						.format(dupsym.line, dupsym.col,
							sym.val, sym.line, sym.col))
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
		raise Exception("[Line {}:{}] Redefinition of {}\n"
						"[Line {}:{}] Previous definition was here"
						.format(dupsym.line, dupsym.col,
							sym.val, sym.line, sym.col))
	localsymboltable.update(argsymboltable)
	return localsymboltable

def type_id(tree, symtab):
	if tree.tok.val not in symtab:
		raise Exception("[Line {}:{}] Found id {}, but it has not been defined"
				.format(tree.tok.line, tree.tok.col, tree.tok.val))
	return symtab[tree.tok.val].type

def type_exp_field(tree, symtab):
	if tree.tok.type == 'id':
		return type_id(tree, symtab)
	t = type_exp_field(tree.children[0], symtab)
	if type(t) is list:
		if tree.tok.type == '.hd':
			return t[0]
		elif tree.tok.type == '.tl':
			return t
		raise Exception("[Line {}:{}] Got list, but cannot apply: {}"
				.format(tree.tok.line, tree.tok.col, tree.tok.type))
	elif type(t) is tuple:
		if tree.tok.type == '.fst':
			return t[0]
		elif tree.tok.type == '.snd':
			return t[1]
		raise Exception("[Line {}:{}] Got tuple, but cannot apply: {}"
						.format(tree.tok.line, tree.tok.col, tree.tok.type))
	
def type_exp_base(tree, symtab):
	if tree.tok.type == 'int':
		return Type('Int')
	elif tree.tok.type == 'bool':
		return Type('Bool')
	elif tree.tok.type == '[]':
		return Type('List')
	elif tree.tok.type == 'FunCall':
		return type_expfunc(tree, symtab)
	elif tree.tok.type == ',':
		return (type_exp(tree.children[0]), type_exp(tree.children[1]))
	else:
		return type_exp_field(tree,symtab)
		
def type_op(fn, in_type, out_type, ops, tree, symtab):
	if tree.tok.type in ops:
		types = map(partial(type_exp, symtab=symtab), tree.children)
		if in_type and not all(t == in_type for t in types):
			raise Exception("[Line {}:{}] Incompatible types for operator {}\n"
							"  Types found: {}"
							.format(tree.tok.line, tree.tok.col,
								tree.tok.type, types))
		return out_type
	return fn(tree, symtab)

type_exp_unint = partial(type_op, type_exp_base,
	Type('Int'), Type('Int'), ['-'])
type_exp_unbool = partial(type_op, type_exp_unint,
	Type('Bool'), Type('Bool'), ['!'])

def type_exp_con(tree, symtab):
	if tree.tok.type == ':':
		t1, t2 = map(type_exp, *tree.children)
		if t2 not in [[t1], Type('List')]:
			raise Exception("[Line {}:{}] Incompatible types for operator {}\n"
							"  Types found: {}"
							.format(tree.tok.line, tree.tok.col,
								tree.tok.type, types))
		return [t1]
	return type_exp_unbool(tree, symtab)

type_exp_mult = partial(type_op, type_exp_con,
	Type('Int'), Type('Int'), ['*', '/', '%'])
type_exp_add = partial(type_op, type_exp_mult,
	Type('Int'), Type('Int'), ['+', '-'])
type_exp_cmp = partial(type_op, type_exp_add,
	Type('Int'), Type('Bool'), ['<', '<=', '>', '>='])
type_exp_eq = partial(type_op, type_exp_cmp,
	None, Type('Bool'), ['==','!='])
type_exp_and = partial(type_op, type_exp_eq,
	Type('Bool'), Type('Bool'), ['&&'])
type_exp_or = partial(type_op, type_exp_and,
	Type('Bool'), Type('Bool'), ['||'])
type_exp = type_exp_or

def type_expargs(tree, symtab):
	''' expects a tree with an arg-node (',') as root '''
	if not tree:
		return []
	return ([type_exp(tree.children[0], symtab)]
			+ type_expargs(tree.children[1], symtab))

def type_expfunc(tree, symtab):
	return type_id(tree.children[0], symtab)

def check_stmt(tree, symtab, rettype):	
	''' expects a tree with a statement node as root '''
	if tree.tok.type == 'Scope':
		check_stmts(tree.children[0], symtab, rettype)
	elif tree.tok.type == 'FunCall':
		type_expfunc(tree, symtab) # needed to confirm the id definition
		received = type_expargs(tree.children[1], symtab)
		expected = symtab[tree.children[0].tok.val].argtype
		if received != expected:
			raise Exception("[Line {}:{}] Incompatible argument types "
							"  for function '{}'.\n"
							"  Types expected: {}\n"
							"  Types found: {}"
							.format(tree.tok.line, tree.tok.col,
								tree.children[0].tok.val, expected, received))
	elif tree.tok.type == 'if' or tree.tok.type == 'while':
		condition = type_exp(tree.children[0], symtab)
		if condition != Type('Bool'):
			raise Exception("[Line {}:{}] Incompatible condition type\n"
							"  Expected expression of type Bool, but got {}"
							.format(tree.tok.line, tree.tok.col, condition))
		check_stmt(tree.children[1], symtab, rettype)
		if tree.tok.type == 'if' and tree.children[2]: # for 'else'-clause
			check_stmt(tree.children[2], symtab, rettype)
	elif tree.tok.type == '=':
		idtype = type_id(tree.children[0], symtab)
		exptype = type_exp(tree.children[1], symtab)
		if idtype != exptype:
			raise Exception("[Line {}:{}] Invalid assignment for id {}\n"
							"  Expected expression of type: {}\n"
							"  But got value of type: {}"
							.format(tree.tok.line, tree.tok.col,
								tree.children[0].tok.val, idtype, exptype))
	elif tree.tok.type == 'return':
		exptype = type_exp(tree.children[0], symtab)
		if rettype != exptype:
			raise Exception("[Line {}:{}] Invalid return type\n"
							"  Function is of type: {}\n"
							"  But returns value of type: {}"
							.format(tree.tok.line, tree.tok.col,
								rettype, exptype))
	
def check_stmts(tree, symboltable, rettype):
	if tree:
		check_stmt(tree.children[0], symboltable, rettype)
		check_stmts(tree.children[1], symboltable, rettype)

def check_functionbinding(tree, globalsymboltable):
	rettype = globalsymboltable[tree.children[1].tok.val].type
	functionsymboltable = create_functiontable(tree)
	for key in set(functionsymboltable.keys()) & set(globalsymboltable.keys()):
		dupsym = symbols[key]
		sys.stderr.write("[Line {}:{}] Warning: redefinition of global {}\n"
						"[Line {}:{}] Previous definition was here"
						.format(dupsym.line, dupsym.col,
							sym.val, sym.line, sym.col))
	symboltable = globalsymboltable.copy()
	symboltable.update(functionsymboltable)
	check_stmts(tree.children[4], symboltable, rettype)

def check_localbinding(tree, globalsymboltable):
	if not tree:
		return
	if tree.children[0].tok == 'FunDecl':
		check_functionbinding(tree.children[0], globalsymboltable)
	check_localbinding(tree.children[1], globalsymboltable)

def check_binding(tree, globalsymboltable=dict()):
	globalsymboltable.update(create_table(tree))
	print_symboltable(globalsymboltable)
	check_localbinding(tree, globalsymboltable)
