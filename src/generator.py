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
	if tree.children[1]:
		return (['ajs 2'] +
			gen_args(tree.children[1], wab, tables) +
			['ajs '+str(-len(tables[tree.children[0].tok.val].argtypes)-2),
			 'bsr ' + tree.children[0].tok.val])
	return ['bsr ' + tree.children[0].tok.val]
		
def gen_exp_id(tree, wab, tables):
	if tree.tok.val in wab[1]:
		return ['ldl ' + str(wab[1][tree.tok.val])]
	return ['ldc ' + str(HEAPBASE + wab[0][tree.tok.val]), 'ldh 0']

def gen_exp_base(tree, wab, tables):
	if tree.tok.type == 'int':
		return ['ldc ' + str(tree.tok.val)]
	elif tree.tok.type == 'bool':
		return ['ldc ' + str(-1 * int(tree.tok.val))] # True = 11....111
	elif tree.tok.type == '[]':
		return ['ldc 0']
	elif tree.tok.type == 'FunCall':
		rettype = tables[tree.children[0].tok.val].type
		result = gen_funcall(tree, wab, tables)
		if rettype != Type('Void'):
			result += ['ldr RR']
		return result
	elif tree.tok.type == ',':
		result = (gen_exp(tree.children[0], wab, tables) +
			gen_exp(tree.children[1], wab, tables))
		return result + ['sth', 'ajs -1', 'sth']
	return gen_exp_id(tree, wab, tables)

def gen_exp_op(tree, wab, tables):
	unops = {'!': ['not'], '-': ['neg'],
		'.hd': ['ldh 0'], '.tl': ['ldh -1'],
		'.fst': ['ldh 0'], '.snd': ['ldh -1']}
	ops = {':': ['sth', 'ajs -1', 'sth'],
		'*': ['mul'], '%': ['mod'], '/': ['div'], '+': ['add'], '-': ['sub'],
		'&&': ['and'], '||': ['or'], '==': ['eq'], '!=': ['ne'],
		'<': ['lt'], '<=': ['le'], '>': ['gt'], '>=': ['ge']}
	if tree.tok.type in ops or tree.tok.type in unops:
		operands = [gen_exp(x, wab, tables) for x in tree.children]
		if len(operands) == 1:
			return reduce(lambda x, y: x + y, operands) + unops[tree.tok.type]
		else:
			return reduce(lambda x, y: x + y, operands) + ops[tree.tok.type]
	return gen_exp_base(tree, wab, tables)

gen_exp = gen_exp_op

def gen_field_assignment(tree, wab, tables):
	offset = -int(tree.tok.type in ['.snd', '.tl'])
	if tree.children[0].tok.type == 'id':
		if tree.children[0].tok.val in wab[1]:
			return ['ldl '+str(wab[1][tree.children[0].tok.val])] + ['ldh '+str(offset)]
		return ['ldc ' + str(HEAPBASE + wab[0][tree.children[0].tok.val])] + ['ldh '+str(offset)]
	return gen_field_assignment(tree.children[0], wab, tables) + ['ldh '+str(offset)]
	
def count_bytes(asms):
	return sum([x.strip().count(' ') + 1 for x in asms])

def gen_stmt(tree, wab, tables):
	if tree.tok.type == 'Scope':
		return gen_stmts(tree.children[0], wab, tables)
	elif tree.tok.type == 'FunCall':
		return gen_funcall(tree, wab, tables)
	elif tree.tok.type == 'if':
		condition = gen_exp(tree.children[0], wab, tables)
		ifstmts = gen_stmt(tree.children[1], wab, tables)
		elsestmts = []
		if tree.children[2]:
			elsestmts = gen_stmt(tree.children[2], wab, tables)
			ifstmts += ['bra ' + str(count_bytes(elsestmts))]
		branch = ['brf ' + str(count_bytes(ifstmts))]
		return condition + branch + ifstmts + elsestmts
	elif tree.tok.type == 'while':
		condition = gen_exp(tree.children[0], wab, tables)
		stmts = gen_stmt(tree.children[1], wab, tables)
		branch = ['brf ' + str(count_bytes(stmts) + 2)] # +2 to jump over bra x
		endbranch = ['bra -' + str(count_bytes(condition + branch + stmts) + 2)]
		return condition + branch + stmts + endbranch
	elif tree.tok.type == '=':
		result = gen_exp(tree.children[1], wab, tables)
		if tree.children[0].tok.type == 'id':
			localvar = tree.children[0].tok.val
			if tree.children[0].tok.val in wab[1]:
				return result + ['stl '+str(wab[1][localvar])]
			return result + ['ldc ' + str(HEAPBASE + wab[0][localvar]), 'sta 0']
		else:
			result += gen_field_assignment(tree.children[0], wab, tables)
			result[-1] = result[-1].replace('ldh', 'sta')
			return result
	elif tree.tok.type == 'return':
		ret = ['unlink', 'ret']
		if not tree.children[0]:
			return ret
		return gen_exp(tree.children[0], wab, tables) + ['str RR'] + ret

def gen_stmts(tree, wab, tables):
	if not tree:
		return []
	return (gen_stmt(tree.children[0], wab, tables) +
		gen_stmts(tree.children[1], wab, tables))

def address_args(tree, wab):
	if tree:
		wab[1][tree.children[1].tok.val] = len(wab[1]) + 1
		address_args(tree.children[2], wab)
		
def gen_locals(tree, wab, tables):
	if not tree:
		return []
	localvar = tree.children[0].children[1].tok.val
	wab[1][localvar] = len(wab[1]) + 1
	return (gen_exp(tree.children[0].children[2], wab, tables) +
		['stl '+str(wab[1][localvar])] +
		gen_locals(tree.children[1], wab, tables))
	
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
	numargs = len(tables[tree.children[1].tok.val].argtypes)
	numlocals = numargs + depth(tree.children[3], 1)
	result += ['link '+str(numlocals)]
	result += gen_locals(tree.children[3], wab, tables)
	result += gen_stmts(tree.children[4], wab, tables)
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
		gen_decls(tree, wab, tables, False) +
		['print:', 'trap 0'] +
		['isEmpty:', 'ldc 0', 'eq'])
	for x in asm:
		fout.write(x+'\n')
	print wab
