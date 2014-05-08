#! /usr/bin/python

from semanticanalysis import Type
from functools import partial

HEAPBASE = 2000 # 7d0, initial value of HP

def gen_args(tree, wab, tables):
	if not tree:
		return []
	return (gen_exp(tree.children[0], wab, tables) +
		gen_args(tree.children[1], wab, tables))

def gen_funcall(tree, wab, tables):
	return (['ajs 2'] +
		gen_args(tree.children[1], wab, tables) +
		['ajs -2', 'bsr ' + tree.children[0].tok.val])
	
def gen_exp_id(tree, wab, tables):
	# global only
	return ['ldc ' + str(HEAPBASE + wab[0][tree.tok.val]), 'ldh 0']

def gen_exp_base(tree, wab, tables):
	if tree.tok.type == 'int':
		return ['ldc ' + str(tree.tok.val)]
	elif tree.tok.type == 'bool':
		return ['ldc ' + str(-1 * int(tree.tok.val))] # True = 11....111
	elif tree.tok.type == '[]':
		return ['ldc 0']
	elif tree.tok.type == 'FunCall':
		rettype = tables['_glob'][tree.children[0].tok.val].type
		result = gen_funcall(tree, wab, tables)
		if rettype != Type('Void'): # TODO test
			result += ['ldr RR']
		return result
	elif tree.tok.type == ',':
		result = (gen_exp(tree.children[0], wab, tables) +
			gen_exp(tree.children[1], wab, tables))
		return result + ['sth', 'ajs -1', 'sth']
	return gen_exp_id(tree, wab, tables)

def gen_exp_op(tree, wab, tables):
	unops = {'!': ['not'], '-': ['neg']}
	ops = {':': ['sth', 'ajs -1', 'sth'],
		'*': ['mul'], '%': ['mod'], '/': ['div'], '+': ['add'], '-': ['sub'],
		'&&': ['and'], '||': ['or'], '==': ['eq'], '!=': ['ne'],
		'<': ['lt'], '<=': ['le'], '>': ['gt'], '>=': ['ge'],
		'.hd': ['ldh 0'], '.tl': ['ldh -1'],
		'.fst': ['ldh 0'], '.snd': ['ldh -1']}
	if tree.tok.type in ops or tree.tok.type in unops:
		operands = [gen_exp(x, wab, tables) for x in tree.children]
		if len(operands) == 1:
			return reduce(lambda x, y: x + y, operands) + unops[tree.tok.type]
		else:
			return reduce(lambda x, y: x + y, operands) + ops[tree.tok.type]
	return gen_exp_base(tree, wab, tables)

gen_exp = gen_exp_op

def gen_stmt(tree, wab, tables):
	print tree.tok.type
	if tree.tok.type == 'Scope':
		return gen_stmts(tree.children[0], wab, tables)
	elif tree.tok.type == 'FunCall':
		return gen_funcall(tree, wab, tables)
	elif tree.tok.type == 'if' or tree.tok.type == 'while':
		return []
	elif tree.tok.type == '=':
		return []
	elif tree.tok.type == 'return':
		if not tree.children[0]:
			return ['unlink', 'ret']
		return gen_exp(tree.children[0], wab, tables) + ['str RR', 'unlink', 'ret']

# elif tree.tok.type == 'if' or tree.tok.type == 'while':
	# 	condition = type_exp(tree.children[0], symtab)
	# 	if condition.unify(Type('Bool')) is None:
	# 		raise Exception("[Line {}:{}] Incompatible condition type\n"
	# 						"  Expected expression of type: Bool\n"
	# 						"  But got value of type: {}"
	# 						.format(tree.tok.line, tree.tok.col, condition))
	# 	returned = False
	# 	if tree.tok.type == 'if' and tree.children[2]: # for 'else'-clause
	# 		returned = check_stmt(tree.children[2], symtab, rettype)
	# 	return check_stmt(tree.children[1], symtab, rettype) and returned
	# elif tree.tok.type == '=':
	# 	fieldtype = type_exp_field(tree.children[0], symtab)
	# 	exptype = type_exp(tree.children[1], symtab)
	# 	if fieldtype.unify(exptype) is None:
	# 		raise Exception("[Line {}:{}] Invalid assignment for id {}\n"
	# 						"  Expected expression of type: {}\n"
	# 						"  But got value of type: {}"
	# 						.format(tree.tok.line, tree.tok.col,
	# 							tree.children[0].tok.val, fieldtype, exptype))

def gen_stmts(tree, wab, tables):
	if not tree:
		return []
	return (gen_stmt(tree.children[0], wab, tables) +
		gen_stmts(tree.children[1], wab, tables))

def address_args(tree, wab):
	if tree:
		wab[1][tree.children[1].tok.val] = len(wab[1])
		address_args(tree.children[2], wab)
		
def gen_locals(tree, wab, tables):
	if not tree:
		return []
	wab[1][tree.children[0].children[1].tok.val] = len(wab[1])
	return (gen_exp(tree.children[0].children[2], wab, tables) +
		gen_locals(tree.children[1], wab, tables))
	# TODO: actually store the gen_exp
	
def depth(tree, index):
	if not tree:
		return 0
	return 1 + depth(tree.children[index], index)

def gen_vardecl(tree, wab, tables):
	return (gen_exp(tree.children[2], wab, tables) +
		['ldc ' + str(HEAPBASE + wab[0][tree.children[1].tok.val]), 'sta 0'])

def gen_fundecl(tree, wab, tables):
	wab[1] = dict()
	address_args(tree.children[2], wab)
	result = [tree.children[1].tok.val+':']
	numlocals = depth(tree.children[2], 2) + depth(tree.children[3], 1)
	result += ['link '+str(numlocals)]
	result += gen_locals(tree.children[3], wab, tables)
	result += gen_stmts(tree.children[4], wab, tables)
	if result[-1] != 'ret':
		result += ['unlink', 'ret']
	return result
	
def gen_decls(tree, wab, tables, vardecls, reserve=False):
	if not tree:
		return []
	result = []
	if tree.children[0].tok == 'FunDecl' and not vardecls:
		result = gen_fundecl(tree.children[0], wab, tables)
	if tree.children[0].tok == 'VarDecl' and vardecls:
		if reserve:
			wab[0][tree.children[0].children[1].tok.val] = len(wab[0])
		else:
			result = gen_vardecl(tree.children[0], wab, tables)
	return result + gen_decls(tree.children[1], wab, tables, vardecls, reserve)
	
def generate_ssm(tree, tables, fout):
	wab = [dict(), dict()] # global and local address book
	asm = (gen_decls(tree, wab, tables, True, True) +
		['ldc '+ str(HEAPBASE + len(wab[0])), 'str HP'] +
		gen_decls(tree, wab, tables, True) + ['halt'] + 
		gen_decls(tree, wab, tables, False))
	for x in asm:
		fout.write(x+'\n')
	print wab
