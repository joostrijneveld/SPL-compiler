#! /usr/bin/env python

import collections
import sys
from functools import partial

Symbol = collections.namedtuple('Symbol', ['line','col','type','argtypes'])

class Type:
	def __init__(self, value):
		self.value = value
	
	@staticmethod
	def from_node(tree): # tree is Type-node
		if tree.tok.type in ['Bool', 'Int', 'Void']:
			return Type(tree.tok.type)
		elif tree.tok.type == 'id':
			return Type(tree.tok.val)
		elif tree.tok.type == ',':
			return Type((Type.from_node(tree.children[0]),
					Type.from_node(tree.children[1])))
		elif tree.tok.type == '[':
			return Type([Type.from_node(tree.children[0])])

	def __repr__(self):
		return repr(self.value)
		
	def __eq__(self, other):
		if self is None or other is None: # needed to compare to 'None'
			return self is other
		# Type([Type(None)] represents the empty list
		# in other words: Type(None) is the content of the empty list
		if self.value == None or other.value == None: 
			return True
		
		for t in [list, tuple]:
			if type(self.value) is t:
				if type(other.value) is t:
					return all(s == o for s, o in zip(self.value, other.value))
				return False
			if type(other.value) is t: # self is not list/tuple at this point
				return False
		
		return self.value == other.value
	
	def unify(self, other):
		''' attempts to unify self and other (necessary for empty lists) '''
		if type(self.value) is tuple and type(other.value) is tuple:
			left = self.value[0].unify(other.value[0])
			right = self.value[1].unify(other.value[1])
			if not (left and right):
				return None
			return Type((left, right))
		if type(self.value) is list and type(other.value) is list:
			result = self.value[0].unify(other.value[0])
			if not result:
				return None
			return Type([result])
		if self == other:
			if self.value == None:
				return other
			return self
		return None
	
	def __neq__(self, other):
		return not self == other
	
	def isEmptyList(self):
		return type(self.value) is list and self.value[0].value == None

def print_symboltable(symboltable):
	print '='*62
	print ("{0: <12} {1: <15} {2: <15} {3: <20}"
			.format('Position', 'Name', 'Type', 'Argtypes'))
	print '-'*62
	for k, v in symboltable.iteritems():
		argvstring =  ", ".join(map(str, v.argtypes)) if v.argtypes != None else None
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
	if type(t.value) is list:
		if tree.tok.type == '.hd':
			return t.value[0]
		elif tree.tok.type == '.tl':
			return t
		raise Exception("[Line {}:{}] Got list, but cannot apply: '{}'"
				.format(tree.tok.line, tree.tok.col, tree.tok.type))
	elif type(t.value) is tuple:
		if tree.tok.type == '.fst':
			return t.value[0]
		elif tree.tok.type == '.snd':
			return t.value[1]
		raise Exception("[Line {}:{}] Got tuple, but cannot apply: '{}'"
						.format(tree.tok.line, tree.tok.col, tree.tok.type))
	raise Exception("[Line {}:{}] Cannot apply '{}' to symbol of type {} "
			.format(tree.tok.line, tree.tok.col, tree.tok.type, t))
	
def type_exp_base(tree, symtab):
	if tree.tok.type == 'int':
		return Type('Int')
	elif tree.tok.type == 'bool':
		return Type('Bool')
	elif tree.tok.type == '[]':
		return Type([Type(None)])
	elif tree.tok.type == 'FunCall':
		t = type_expfunc(tree, symtab) # includes existence-check
		gentab = check_funcall(tree, symtab)
		return apply_gentab(tree, t, gentab)
	elif tree.tok.type == ',':
		return Type((type_exp(tree.children[0], symtab),
			type_exp(tree.children[1], symtab)))
	else:
		return type_exp_field(tree,symtab)
		
def type_op(fn, in_types, out_type, ops, tree, symtab):
	if tree.tok.type in ops:
		rev_types = map(partial(type_exp, symtab=symtab), tree.children)
		gentab = dict()
		if not all(apply_generics(e, r, gentab) for e, r in zip(in_types, rev_types)):
			raise Exception("[Line {}:{}] Incompatible types for operator {}\n"
							"  Types expected: {}\n"
							"  Types found: {}"
							.format(tree.tok.line, tree.tok.col, tree.tok.type,
								', '.join(map(str, in_types)),
								', '.join(map(str, rev_types))))
		return out_type
	return fn(tree, symtab)

type_exp_unint = partial(type_op, type_exp_base,
	[Type('Int')], Type('Int'), ['-'])
type_exp_unbool = partial(type_op, type_exp_unint,
	[Type('Bool')], Type('Bool'), ['!'])

def type_exp_con(tree, symtab):
	if tree.tok.type == ':':
		t1, t2 = map(partial(type_exp, symtab=symtab), tree.children)
		if not t2.isEmptyList() and not t2 == Type([t1]):
			raise Exception("[Line {}:{}] Incompatible types for operator {}\n"
							"  Types expected: t, [t]\n"
							"  Types found: {}, {}"
							.format(tree.tok.line, tree.tok.col,
								tree.tok.type, t1, t2))
		if t1.isEmptyList() and not t2.isEmptyList(): # adding an empty list (i.e. [] : (5 : []) : [])
			return t2
		return Type([t1])
	return type_exp_unbool(tree, symtab)

type_exp_mult = partial(type_op, type_exp_con,
	[Type('Int'), Type('Int')], Type('Int'), ['*', '/', '%'])
type_exp_add = partial(type_op, type_exp_mult,
	[Type('Int'), Type('Int')], Type('Int'), ['+', '-'])
type_exp_cmp = partial(type_op, type_exp_add,
	[Type('Int'), Type('Int')], Type('Bool'), ['<', '<=', '>', '>='])
type_exp_eq = partial(type_op, type_exp_cmp,
	[Type('t'), Type('t')], Type('Bool'), ['==','!='])
type_exp_and = partial(type_op, type_exp_eq,
	[Type('Bool'), Type('Bool')], Type('Bool'), ['&&'])
type_exp_or = partial(type_op, type_exp_and,
	[Type('Bool'), Type('Bool')], Type('Bool'), ['||'])
type_exp = type_exp_or

def type_expargs(tree, symtab):
	''' expects a tree with an arg-node (',') as root '''
	if not tree:
		return []
	return ([type_exp(tree.children[0], symtab)]
			+ type_expargs(tree.children[1], symtab))

def type_expfunc(tree, symtab):
	return type_id(tree.children[0], symtab)

def apply_gentab(tree, t, gentab):
	'''replaces generics that occur in t with their literal type from gentab'''
	if t.value in ['Int', 'Bool', 'Void']:
		return t
	if type(t.value) is str:
		if t.value not in gentab:
			raise Exception("[Line {}:{}] Generic return type {} is not bound "
							"by arguments for function '{}', so cannot be resolved."
							.format(tree.tok.line, tree.tok.col, t,
								tree.children[0].tok.val))
		return gentab[t.value]
	if type(t.value) is tuple:
		return Type((apply_gentab(tree, t.value[0], gentab),
				apply_gentab(tree, t.value[1], gentab)))
	if type(t.value) is list:
		return Type([apply_gentab(tree, t.value[0], gentab)])

def apply_generics(gen_type, lit_type, gentab):
	if gen_type.value in ['Int', 'Bool']:
		return gen_type == lit_type
	if type(gen_type.value) is str:
		if gen_type.value in gentab:
			result = gentab[gen_type.value].unify(lit_type)
			if not result:
				return False
			gentab[gen_type.value] = result
		else:
			gentab[gen_type.value] = lit_type
		return True
	for t in [list, tuple]:
		if type(gen_type.value) is t:
			if type(lit_type.value) is t:
				return all(apply_generics(s, o, gentab) for s, o in zip(gen_type.value, lit_type.value))
			return False
		if type(lit_type.value) is t: # gen_type is not list/tuple at this point
			return False

def check_funcall(tree, symtab):
	received = type_expargs(tree.children[1], symtab)
	expected = symtab[tree.children[0].tok.val].argtypes
	if not len(expected) == len(received):
		raise Exception("[Line {}:{}] Incompatible number of arguments "
						"for function '{}'.\n"
						"  Arguments expected: {}\n"
						"  Arguments found: {}"
						.format(tree.tok.line, tree.tok.col,
							tree.children[0].tok.val,
							len(expected), len(received)))
	gentab = dict()
	if (not all(apply_generics(e, r, gentab)
		for e, r in zip(expected, received))):
		raise Exception("[Line {}:{}] Incompatible argument types "
						"for function '{}'.\n"
						"  Types expected: {}\n"
						"  Types found: {}"
						.format(tree.tok.line, tree.tok.col,
							tree.children[0].tok.val,
							', '.join(map(str, expected)),
							', '.join(map(str, received))))
	return gentab

def check_stmt(tree, symtab, rettype):	
	''' expects a tree with a statement node as root '''
	if tree.tok.type == 'Scope':
		return check_stmts(tree.children[0], symtab, rettype)
	elif tree.tok.type == 'FunCall':
		type_expfunc(tree, symtab) # needed to confirm the id definition
		check_funcall(tree, symtab)
	elif tree.tok.type == 'if' or tree.tok.type == 'while':
		condition = type_exp(tree.children[0], symtab)
		if not condition == Type('Bool'):
			raise Exception("[Line {}:{}] Incompatible condition type\n"
							"  Expected expression of type Bool, but got {}"
							.format(tree.tok.line, tree.tok.col, condition))
		returned = False
		if tree.tok.type == 'if' and tree.children[2]: # for 'else'-clause
			returned = check_stmt(tree.children[2], symtab, rettype)
		return check_stmt(tree.children[1], symtab, rettype) and returned
	elif tree.tok.type == '=':
		fieldtype = type_exp_field(tree.children[0], symtab)
		exptype = type_exp(tree.children[1], symtab)
		if not fieldtype == exptype:
			raise Exception("[Line {}:{}] Invalid assignment for id {}\n"
							"  Expected expression of type: {}\n"
							"  But got value of type: {}"
							.format(tree.tok.line, tree.tok.col,
								tree.children[0].tok.val, fieldtype, exptype))
	elif tree.tok.type == 'return':
		if not tree.children[0]:
			exptype = Type('Void')
		else:
			exptype = type_exp(tree.children[0], symtab)
		if not rettype == exptype:
			raise Exception("[Line {}:{}] Invalid return type\n"
							"  Function is of type: {}\n"
							"  But returns value of type: {}"
							.format(tree.tok.line, tree.tok.col,
								rettype, exptype))
		return True
	
def check_stmts(tree, symboltable, rettype):
	if tree:
		returned = check_stmt(tree.children[0], symboltable, rettype)
		return returned or check_stmts(tree.children[1], symboltable, rettype)

def check_vardecl(tree, symtab):
	vartype = Type.from_node(tree.children[0])
	exptype = type_exp(tree.children[2], symtab)
	if not vartype == exptype:
		raise Exception("[Line {}:{}] Invalid assignment for id {}\n"
						"  Expected expression of type: {}\n"
						"  But got value of type: {}"
						.format(tree.children[1].tok.line, tree.children[1].tok.col,
							tree.children[1].tok.val, vartype, exptype))
		
def check_vardecls(tree, symboltable):
	if tree:
		check_vardecl(tree.children[0], symboltable)
		check_vardecls(tree.children[1], symboltable)

def check_functionbinding(tree, globalsymboltable):
	rettype = globalsymboltable[tree.children[1].tok.val].type
	functionsymboltable = create_functiontable(tree)
	for key in set(functionsymboltable.keys()) & set(globalsymboltable.keys()):
		dupsym = functionsymboltable[key]
		sys.stderr.write("[Line {}:{}] Warning: redefinition of global {}\n"
						"[Line {}:{}] Previous definition was here\n"
						.format(dupsym.line, dupsym.col, key,
							globalsymboltable[key].line, globalsymboltable[key].col))
	symboltable = globalsymboltable.copy()
	symboltable.update(functionsymboltable)
	print_symboltable(symboltable)
	check_vardecls(tree.children[3], symboltable)
	returned = check_stmts(tree.children[4], symboltable, rettype)
	if not returned and not rettype == Type('Void'):
		raise Exception("[Line {}:{}] Missing return statement "
						"in a non-Void function"
						.format(tree.children[1].tok.line,
								tree.children[1].tok.col))

def check_localbinding(tree, globalsymboltable):
	if not tree:
		return
	if tree.children[0].tok == 'FunDecl':
		check_functionbinding(tree.children[0], globalsymboltable)
	elif tree.children[0].tok == 'VarDecl':
		check_vardecl(tree.children[0], globalsymboltable)
	check_localbinding(tree.children[1], globalsymboltable)

def check_binding(tree, globalsymboltable=dict()):
	globalsymboltable.update(create_table(tree))
	print_symboltable(globalsymboltable)
	check_localbinding(tree, globalsymboltable)
