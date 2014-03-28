#! /usr/bin/env python

from collections import deque # for an efficient popleft()
from functools import partial
from scanner import Token

class Node:
	def __init__(self, tok, *children):
		self.tok = tok
		self.children = children
		
	def __repr__(self, depth = 0):
		ret = "\t"*depth+repr(self.tok)+"\n"
		for c in self.children:
			ret += c.__repr__(depth + 1) if c else "\t"*(depth+1)+str(c)+"\n"
		return ret
	
	def __str__(self):
		if type(self.tok) is not Token:
			return repr(self)
		if self.tok.type in ['Int', 'Bool', 'Void']:
			return self.tok.type
		elif self.tok.type == ',':
			return '('+ str(self.children[0]) + ', ' + str(self.children[1]) +')'
		elif self.tok.type == '[':
			return '[' + str(self.children[0]) + ']'
		elif self.tok.type == 'id':
			return self.tok.val
		return repr(self)

def pop_token(tokens, literal):
	tok = tokens.popleft()
	if tok.type != literal:
		raise Exception("[Line {}:{}] Expected '{}', but got: {}"
						.format(tok.line, tok.col, literal, tok.type))
	return tok

def parse_spl(tokens):
	if not tokens:
		return None	
	return Node('Decl', parse_decl(tokens), parse_spl(tokens))	

def parse_decl(tokens):
	if tokens[0].type == 'Void': # which immediately implies a FunDecl
		tok = pop_token(tokens, 'Void')
		return parse_fundecl(Node(tok), tokens)
	t = parse_type(tokens)
	if tokens[1].type == '=': # so we're actually in a VarDecl
		return parse_vardecl(tokens, t)
	return parse_fundecl(t, tokens)
		
def parse_vardecl(tokens, t = None):
	if not t:
		t = parse_type(tokens)
	varname = pop_token(tokens, 'id')
	pop_token(tokens, '=')
	exp = parse_exp(tokens)
	pop_token(tokens, ';')
	return Node('VarDecl', t, Node(varname), exp)

def start_of_vardecl(tokens):
	if tokens[0].type in ['Int', 'Bool', '(', '[']:
		return True
	return tokens[0].type == 'id' and tokens[1].type == 'id'

def parse_vardecl_list(tokens):
	if not start_of_vardecl(tokens):
		return None
	return Node(';', parse_vardecl(tokens), parse_vardecl_list(tokens))	

def parse_fundecl(rettype, tokens):
	funname = pop_token(tokens, 'id')
	pop_token(tokens, '(')
	fargs = None
	if tokens[0].type != ')':
		fargs = parse_fargs(tokens)
	pop_token(tokens, ')')
	pop_token(tokens, '{')
	vardecls = parse_vardecl_list(tokens)
	stmts = parse_stmt_list(tokens)
	if not stmts:
		raise Exception("[Line {}:{}] Expected statement, but got: {}"
						.format(tokens[0].line, tokens[0].col, tokens[0].type))
	pop_token(tokens, '}')
	return Node('FunDecl', rettype, Node(funname), fargs, vardecls, stmts)

def parse_type(tokens):
	tok = tokens.popleft()
	if tok.type in ['Int', 'Bool', 'id']:
		return Node(tok)
	if tok.type == '(':
		t_left = parse_type(tokens)
		tok = pop_token(tokens, ',')
		t_right = parse_type(tokens)
		pop_token(tokens, ')')
		return Node(tok, t_left, t_right)
	if tok.type == '[':
		t_left = parse_type(tokens)
		pop_token(tokens,']')
		return Node(tok, t_left)
	raise Exception("[Line {}:{}] Expected new type but got: {}"
					.format(tok.line, tok.col, tok.type))
		
def parse_stmt_list(tokens):
	if tokens[0].type == '}':
		return None
	return Node(';', parse_stmt(tokens), parse_stmt_list(tokens))

def parse_stmt(tokens):
	tok = tokens.popleft()
	if tok.type == 'id':
		if tokens[0].type == '(': # for ExpFunc
			result = parse_exp_func(tok, tokens)
		else: # for ExpField
			exp_field = parse_exp_field(tok, tokens)
			littok = pop_token(tokens, '=')
			result = Node(littok, exp_field, parse_exp(tokens))
		pop_token(tokens, ';')
		return result
	elif tok.type == 'if':
		pop_token(tokens, '(')
		condition = parse_exp(tokens)
		pop_token(tokens, ')')
		if_stmt = parse_stmt(tokens)
		if tokens and tokens[0].type == 'else': # optional 'else'
			pop_token(tokens, 'else')
			return Node(tok, condition, if_stmt, parse_stmt(tokens))
		return Node(tok, condition, if_stmt, None)
	elif tok.type == 'while':
		pop_token(tokens, '(')
		condition = parse_exp(tokens)
		pop_token(tokens, ')')
		return Node(tok, condition, parse_stmt(tokens))
	elif tok.type == 'return':
		if tokens[0].type == ';':
			pop_token(tokens, ';')
			return Node(tok, None)
		result = parse_exp(tokens)
		pop_token(tokens, ';')
		return Node(tok, result)
	elif tok.type == '{':
		stmt_scope = parse_stmt_list(tokens)			
		pop_token(tokens, '}')
		return Node('Scope',stmt_scope)
	raise Exception("[Line {}:{}] Expected new statement, but got: {}"
					.format(tok.line, tok.col, tok.type))
		
def parse_exp_field(id_tok, tokens):
	t = Node(id_tok)
	while tokens and tokens[0].type in ['.hd', '.tl', '.fst', '.snd']:
		tok = tokens.popleft()
		t = Node(tok, t)
	return t

def parse_exp_func(id_tok, tokens):
	t_left = Node(id_tok)
	pop_token(tokens, '(')
	t_right = None
	if tokens[0].type != ')':
		t_right = parse_exp_args(tokens)
	pop_token(tokens, ')')
	return Node('FunCall', t_left, t_right)

def parse_exp_args(tokens):
	t_left = parse_exp(tokens)
	if tokens[0].type == ',':
		pop_token(tokens, ',')
		return Node(',', t_left, parse_exp_args(tokens))
	return Node(',', t_left, None)

def parse_fargs(tokens):
	argtype = parse_type(tokens)
	argname = pop_token(tokens, 'id')
	if tokens[0].type == ',':
		pop_token(tokens, ',')
		return Node(',', argtype, Node(argname), parse_fargs(tokens))
	return Node(',', argtype, Node(argname), None)

def parse_exp_base(tokens):
	tok = tokens.popleft()
	if tok.type == 'id':
		if tokens[0].type == '(': # for ExpFunc
			result = parse_exp_func(tok, tokens)
			return result
		return parse_exp_field(tok, tokens)
	elif tok.type in ['int', 'bool', '[]']:
		return Node(tok)
	elif tok.type == '(':
		t_left = parse_exp(tokens)
		t_right = None
		tok = tokens.popleft()
		if tok.type == ',': # we're dealing with a tuple
			t_right = parse_exp(tokens)
			pop_token(tokens, ')')
			return Node(tok, t_left, t_right)
		elif tok.type == ')': # or with an exp in brackets
			if not t_right:
				return t_left
		raise Exception("[Line {}:{}] Expected ')' or ',', but got: {}"
						.format(tok.line, tok.col, tok.type))
	raise Exception("[Line {}:{}] Expected new expression, but got: {}"
					.format(tok.line, tok.col, tok.type))

def parse_exp_un(tokens):
	if tokens and tokens[0].type in ['-', '!']:
		tok = tokens.popleft()
		return Node(tok, parse_exp_un(tokens))
	return parse_exp_base(tokens)

def parse_exp_con(tokens):
	t = parse_exp_un(tokens)
	if tokens and tokens[0].type == ':':
		tok = pop_token(tokens, ':')
		return Node(tok, t, parse_exp_con(tokens))
	return t
	
def tail_recursion(fn, ops, tokens):
	# fn is the next function for the recursive descent
	t = fn(tokens)
	while tokens and tokens[0].type in ops:
		tok = tokens.popleft()
		t_right = fn(tokens)
		t = Node(tok, t, t_right)
	return t
	
# partial function application, so that we can pass a function reference down
parse_exp_mult = partial(tail_recursion, parse_exp_con, ['*', '/', '%'])
parse_exp_add  = partial(tail_recursion, parse_exp_mult, ['+', '-'])
parse_exp_cmp  = partial(tail_recursion, parse_exp_add, ['<', '<=', '>', '>='])
parse_exp_eq   = partial(tail_recursion, parse_exp_cmp, ['==','!='])
parse_exp_and  = partial(tail_recursion, parse_exp_eq, ['&&'])
parse_exp_or   = partial(tail_recursion, parse_exp_and, ['||'])
parse_exp      = parse_exp_or

def build_tree(tokens):
	tokens = deque(tokens) # to allow popleft
	try:
		tree = parse_spl(tokens)
	except IndexError:
		raise Exception("Unexpectedly reached end of file.")
	if not tree:
		raise Exception("Unable to parse: program is empty?")
	if tokens:
		raise Exception("[Line {}:{}] Done parsing, but there are still tokens remaining. Next token: {}"
						.format(tokens[0].line, tokens[0].col, tokens[0].type))
	return tree
	