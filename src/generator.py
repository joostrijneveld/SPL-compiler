#! /usr/bin/python

from functools import partial

HEAPBASE = 2000 # 7d0, initial value of HP

def gen_exp_field(tree, gwab, tables):
	return [] #TODO

def gen_exp_base(tree, gwab, tables):
	if tree.tok.type == 'int':
		return ['ldc ' + str(tree.tok.val)]
	elif tree.tok.type == 'bool':
		return ['ldc ' + str(int(tree.tok.val))] # converts True/False to 1/0
	elif tree.tok.type == '[]':
		return ['ldc 0']
	elif tree.tok.type == 'FunCall':
		return [] #TODO
	elif tree.tok.type == ',':
		result = (gen_exp(tree.children[0], gwab, tables) +
			gen_exp(tree.children[1], gwab, tables))
		gwab['_offset'] += 2
		return result + ['sth', 'ajs -1', 'sth'] # maybe point to other elem
	return gen_exp_field(tree, gwab, tables)

def gen_exp_con(tree, gwab, tables):
	return gen_exp_base(tree, gwab, tables)

def gen_exp_op(tree, gwab, tables):
	ops = {'!': 'not', '-': 'neg',
		'*': 'mul', '%': 'mod', '/':'div', '+': 'add', '-': 'sub',
		'&&': 'and', '||': 'or', '==': 'eq', '!=': 'ne',
		'<': 'lt', '<=': 'le', '>': 'gt', '>=': 'ge' }
	for op in ops:
		if tree.tok.type == op:
			operands = (map(lambda x: gen_exp_op(x, gwab, tables), 
			# operands = (map(partial(gen_exp_op, gwab=gwab, tables=tables), 
				tree.children))
			return reduce(lambda x, y: x + y, operands) + [op[tree.tok.type]]
	return gen_exp_con(tree, gwab, tables)

gen_exp = gen_exp_op	
	
def gen_vardecl(tree, gwab, tables):
	return (gen_exp(tree.children[2], gwab, tables) +
		['ldc ' + str(HEAPBASE + gwab[tree.children[1].tok.val]), 
		'ldrr R6 HP',
		'str HP',
		'sth',
		'ldrr HP R6',
		'ajs -1'])

def gen_fundecl(tree, gwab, tables):
	pass

def gen_decls(tree, gwab, tables, vardecls, reserve=False):
	if not tree:
		return []
	result = []
	if tree.children[0].tok == 'FunDecl' and not vardecls:
		pass
	if tree.children[0].tok == 'VarDecl' and vardecls:
		if reserve:
			gwab[tree.children[0].children[1].tok.val] = len(gwab)
		else:
			result += gen_vardecl(tree.children[0], gwab, tables)
	return result + gen_decls(tree.children[1], gwab, tables, vardecls, reserve)
	
def generate_ssm(tree, tables, fout):
	gwab = dict() # global address book
	asm = (gen_decls(tree, gwab, tables, True, True) +
		['ldc '+ str(HEAPBASE + len(gwab)),
		'str HP'] +
		gen_decls(tree, gwab, tables, True) +
		gen_decls(tree, gwab, tables, False))
	for x in asm:
		fout.write(x+'\n')
	print gwab