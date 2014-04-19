#! /usr/bin/env python

import collections
import sys
from functools import partial

Symbol = collections.namedtuple('Symbol', ['line','col','type','argtypes'])

class Type:
	def __init__(self, value):
		self.value = value
	
	@staticmethod
	def from_node(tree): # tree is a Type-node
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
	
	def unify(self, other):
		''' attempts to unify non-generic types (necessary for empty lists) '''
		if type(self.value) is tuple and type(other.value) is tuple:
			left = self.value[0].unify(other.value[0])
			right = self.value[1].unify(other.value[1])
			if left is None or right is None:
				return None
			return Type((left, right))
		if type(self.value) is list and type(other.value) is list:
			result = self.value[0].unify(other.value[0])
			if result is None:
				return None
			return Type([result])
		if type(self.value) is str and type(other.value) is str:
			if self.value == other.value:
				return self
			return None
		if self.value == None:
			return other
		if other.value == None:
			return self
		return None

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
		oldsym = symbols[sym.val]
		raise Exception("[Line {}:{}] Redefinition of {}\n"
						"[Line {}:{}] Previous definition was here"
						.format(sym.line, sym.col,
							sym.val, oldsym.line, oldsym.col))
	symbols.update({sym.val : Symbol(sym.line, sym.col, t, argtypes)})

def create_table(tree, symtab):
	''' expects a tree with a Decl-node as root '''
	if not tree:
		return symtab
	t = Type.from_node(tree.children[0].children[0])
	sym = tree.children[0].children[1].tok
	argtypes = None  # VarDecls do not have arguments
	if tree.children[0].tok == 'FunDecl':
		argtypes = find_argtypes(tree.children[0].children[2])
	if tree.children[0].tok == 'VarDecl':
		check_vardecl(tree.children[0], symtab)
	update_symbols(symtab, sym, t, argtypes)
	return create_table(tree.children[1], symtab)

def create_argtable(tree, symtab):
	''' expects a tree with an arg-node (',') as root '''
	if not tree:
		return symtab
	t = Type.from_node(tree.children[0])
	sym = tree.children[1].tok
	update_symbols(symtab, sym, t, None)
	return create_argtable(tree.children[2], symtab)

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
			raise Exception("[Line {}:{}] Incompatible types for operator '{}'\n"
							"  Types expected: {}\n"
							"  Types found: {}"
							.format(tree.tok.line, tree.tok.col, tree.tok.type,
								', '.join(map(str, in_types)),
								', '.join(map(str, rev_types))))
		return apply_gentab(tree, out_type, gentab)
	return fn(tree, symtab)

type_exp_unint = partial(type_op, type_exp_base,
	[Type('Int')], Type('Int'), ['-'])
type_exp_unbool = partial(type_op, type_exp_unint,
	[Type('Bool')], Type('Bool'), ['!'])
type_exp_con = partial(type_op, type_exp_unbool,
	[Type('t'), Type([Type('t')])], Type([Type('t')]), [':'])
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
			raise Exception("[Line {}:{}] Generic return type {} not bound by "
							"arguments of function '{}', so cannot be resolved."
							.format(tree.tok.line, tree.tok.col, t,
								tree.children[0].tok.val))
		return gentab[t.value]
	if type(t.value) is tuple:
		return Type((apply_gentab(tree, t.value[0], gentab),
				apply_gentab(tree, t.value[1], gentab)))
	if type(t.value) is list:
		return Type([apply_gentab(tree, t.value[0], gentab)])

def apply_generics(gen_type, lit_type, gentab):
	''' checks if gen_type can be applied to lit_type, updates gentab '''
	if gen_type.value in ['Int', 'Bool']:
		return gen_type.unify(lit_type) is not None
	if type(gen_type.value) is str: 
		if gen_type.value in gentab:
			result = gentab[gen_type.value].unify(lit_type)
			if not result:
				return False
			gentab[gen_type.value] = result
		else:
			gentab[gen_type.value] = lit_type
		return True
	if type(gen_type.value) is tuple and type(lit_type.value) is tuple:
		return (apply_generics(gen_type.value[0], lit_type.value[0], gentab)
			and apply_generics(gen_type.value[1], lit_type.value[1], gentab))
	if type(gen_type.value) is list and type(lit_type.value) is list:
		return apply_generics(gen_type.value[0], lit_type.value[0], gentab)
	return False

def check_funcall(tree, symtab):
	expected = symtab[tree.children[0].tok.val].argtypes
	if expected == None:
		raise Exception("[Line {}:{}] '{}' is a variable, not a function."
						.format(tree.tok.line, tree.tok.col,
							tree.children[0].tok.val))
	received = type_expargs(tree.children[1], symtab)
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
		if condition.unify(Type('Bool')) is None:
			raise Exception("[Line {}:{}] Incompatible condition type\n"
							"  Expected expression of type: Bool\n"
							"  But got value of type: {}"
							.format(tree.tok.line, tree.tok.col, condition))
		returned = False
		if tree.tok.type == 'if' and tree.children[2]: # for 'else'-clause
			returned = check_stmt(tree.children[2], symtab, rettype)
		return check_stmt(tree.children[1], symtab, rettype) and returned
	elif tree.tok.type == '=':
		fieldtype = type_exp_field(tree.children[0], symtab)
		exptype = type_exp(tree.children[1], symtab)
		if fieldtype.unify(exptype) is None:
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
		if rettype.unify(exptype) is None:
			raise Exception("[Line {}:{}] Invalid return type\n"
							"  Function is of type: {}\n"
							"  But returns value of type: {}"
							.format(tree.tok.line, tree.tok.col,
								rettype, exptype))
		return True
	
def check_stmts(tree, symboltable, rettype):
	if tree:
		returned = check_stmt(tree.children[0], symboltable, rettype)
		if returned and tree.children[1] is not None:
			raise Exception("[Line {}:{}] Unreachable code detected\n"
							"  If this is intentional, enclose it in comments"
							.format(tree.children[1].children[0].tok.line,
								tree.children[1].children[0].tok.col))
		return returned or check_stmts(tree.children[1], symboltable, rettype)

def check_vardecl(tree, symtab):
	vartype = Type.from_node(tree.children[0])
	exptype = type_exp(tree.children[2], symtab)
	if vartype.unify(exptype) is None:
		raise Exception("[Line {}:{}] Invalid assignment for id {}\n"
						"  Expected expression of type: {}\n"
						"  But got value of type: {}"
						.format(tree.children[1].tok.line,
							tree.children[1].tok.col, tree.children[1].tok.val,
							vartype, exptype))

def check_functionbinding(tree, globalsymboltable):
	rettype = globalsymboltable[tree.children[1].tok.val].type
	functionsymboltable = create_argtable(tree.children[2], dict())
	functionsymboltable = create_table(tree.children[3], functionsymboltable)
	for key in set(functionsymboltable.keys()) & set(globalsymboltable.keys()):
		dupsym = functionsymboltable[key]
		sys.stderr.write("[Line {}:{}] Warning: redefinition of global {}\n"
						"[Line {}:{}] Previous definition was here\n"
						.format(dupsym.line, dupsym.col, key,
							globalsymboltable[key].line,
							globalsymboltable[key].col))
	symboltable = globalsymboltable.copy()
	symboltable.update(functionsymboltable)
	print_symboltable(symboltable)
	returned = check_stmts(tree.children[4], symboltable, rettype)
	if not returned and rettype.unify(Type('Void')) is None:
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
	globalsymboltable.update(create_table(tree, dict()))
	print_symboltable(globalsymboltable)
	check_localbinding(tree, globalsymboltable)
