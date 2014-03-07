#! /usr/bin/env python

from collections import deque # superefficient popleft
from functools import partial

class Node:
	def __init__(self, val, *children):
		self.val = val
		self.children = children
		
	def __repr__(self, depth = 0):
		ret = ''
		ret += "\t"*depth+repr(self.val)+"\n"
		for c in self.children:
			ret += c.__repr__(depth + 1) if c else "\t"*(depth+1)+c.__repr__()+"\n"
		return ret

def pop_literal_token(tokens, literal):
	tok = tokens.popleft()
	if tok != literal:
		raise Exception("Expected '{}', but got: {}".format(literal, tok))
	return tok

def is_id(tok):
	return type(tok) is tuple and tok[0] == 'id'

def pop_id(tokens):
	tok = tokens.popleft()
	if not is_id(tok):
		raise Exception("Expected id, but got: {}".format(tok))
	return tok

def parse_spl(tokens):
	if not tokens:
		return None	
	return Node('Decl', parse_decl(tokens), parse_spl(tokens))	

def parse_decl(tokens):
	if tokens[0] == 'Void': # which immediately implies a FunDecl
		tokens.popleft()
		return parse_fundecl(Node('Void'), tokens)
	t = parse_type(tokens)
	if tokens[1] == '=': # so we're actually in a VarDecl
		return parse_vardecl(tokens, t)
	return parse_fundecl(t, tokens)
		
def parse_vardecl(tokens, t = None):
	if not t:
		t = parse_type(tokens)
	varname = pop_id(tokens)
	pop_literal_token(tokens, '=')
	exp = parse_exp(tokens)
	pop_literal_token(tokens, ';')
	return Node('VarDecl', t, Node(varname), exp)

def start_of_vardecl(tokens):
	if tokens[0] in ['Int', 'Bool', '(', '[']:
		return True
	elif is_id(tokens[0]):
		return is_id(tokens[1])
	return False

def parse_vardecl_list(tokens):
	if not start_of_vardecl(tokens):
		return None
	return Node(';', parse_vardecl(tokens), parse_vardecl_list(tokens))	

def parse_fundecl(rettype, tokens):
	funname = pop_id(tokens)
	pop_literal_token(tokens, '(')
	fargs = None
	if tokens[0] != ')':
		fargs = parse_fargs(tokens)
	pop_literal_token(tokens, ')')
	pop_literal_token(tokens, '{')
	vardecls = parse_vardecl_list(tokens)
	stmts = parse_stmt_list(tokens)
	if not stmts:
		raise Exception("Expected statement, but got: {}".format(tokens[0]))
	pop_literal_token(tokens, '}')
	return Node('FunDecl', rettype, Node(funname), fargs, vardecls, stmts)

def parse_type(tokens):
	tok = tokens.popleft()
	if tok in ['Int', 'Bool'] or is_id(tok):
		return Node(tok)
	if tok == '(':
		t_left = parse_type(tokens)
		pop_literal_token(tokens,',')
		t_right = parse_type(tokens)
		pop_literal_token(tokens,')')
		return Node(',', t_left, t_right)
	if tok == '[':
		t_left = parse_type(tokens)
		pop_literal_token(tokens,']')
		return Node('[]', t_left)
	raise Exception("Expected new type but got: {}".format(tok))
		
def parse_stmt_list(tokens):
	if tokens[0] == '}':
		return None
	return Node(';', parse_stmt(tokens), parse_stmt_list(tokens))

def parse_stmt(tokens):
	try:
		tok = tokens.popleft()
		if is_id(tok):
			if tokens[0] == '(': # for ExpFunc
				result = parse_exp_func(tok, tokens)
			else: # for ExpField
				exp_field = parse_exp_field(tok, tokens)
				pop_literal_token(tokens, '=')
				result = Node('=', exp_field, parse_exp(tokens))
			pop_literal_token(tokens, ';')
			return result
		elif tok == 'if':
			pop_literal_token(tokens, '(')
			condition = parse_exp(tokens)
			pop_literal_token(tokens, ')')
			if_stmt = parse_stmt(tokens)
			if tokens and tokens[0] == 'else': # optional else
				tokens.popleft()
				return Node('if', condition, if_stmt, parse_stmt(tokens))
			return Node('if', condition, if_stmt, None)
		elif tok == 'while':
			pop_literal_token(tokens, '(')
			condition = parse_exp(tokens)
			pop_literal_token(tokens, ')')
			return Node('while', condition, parse_stmt(tokens))
		elif tok == 'return':
			if tokens[0] == ';':
				pop_literal_token(tokens, ';')
				return Node('return', None)
			result = parse_exp(tokens)
			pop_literal_token(tokens, ';')
			return Node('return', result)
		elif tok == '{':
			stmt_scope = parse_stmt_list(tokens)			
			pop_literal_token(tokens, '}')
			return Node('{}',stmt_scope)
		raise Exception("Expected new statement, but got: {}".format(tok))
	except IndexError:
		raise Exception("Unfinished statement, but ran out of tokens.")
		
def parse_exp_field(id_tok, tokens):
	t = Node(id_tok)
	while tokens and tokens[0] in ['.hd', '.tl', '.fst', '.snd']:
		tok = tokens.popleft()
		t = Node(tok, t)
	return t

def parse_exp_func(id_tok, tokens):
	t_left = Node(id_tok)
	pop_literal_token(tokens, '(') # pop off the '(' that was tested for in parse_exp_base
	t_right = None
	if tokens[0] != ')':
		t_right = parse_exp_args(tokens)
	pop_literal_token(tokens, ')')
	return Node('FunCall', t_left, t_right)

def parse_exp_args(tokens):
	t_left = parse_exp(tokens)
	if tokens[0] == ',':
		tokens.popleft()
		return Node(',', t_left, parse_exp_args(tokens))
	return Node(',', t_left, None)

def parse_fargs(tokens):
	argtype = parse_type(tokens)
	argname = pop_id(tokens)
	if tokens[0] == ',':
		tokens.popleft()
		return Node(',', argtype, Node(argname), parse_fargs(tokens))
	return Node(',', argtype, Node(argname), None)

def parse_exp_base(tokens):
	# Parses the first expression from tokens and returns it as a parse tree
	tok = tokens.popleft()
	if is_id(tok):
		if tokens[0] == '(': # for ExpFunc
			result = parse_exp_func(tok, tokens)
			return result
		return parse_exp_field(tok, tokens)
	elif type(tok) is tuple and tok[0] in ['int', 'bool']:
		return Node(tok)
	elif tok == '[':
		tok = tokens.popleft()
		if tok == ']':
			return Node('[]')
		raise Exception("Expected ']', but got: {}".format(tok))
	elif tok == '(':
		t_left = parse_exp(tokens)
		t_right = None
		tok = tokens.popleft()
		if tok == ',': # we're dealing with a tuple
			t_right = parse_exp(tokens)
			tok = tokens.popleft()
			if tok == ')':
				return Node(',', t_left, t_right)
			raise Exception("Expected ')', but got: {}".format(tok))
		elif tok == ')':
			if not t_right:
				return t_left
		raise Exception("Expected ')' or ',', but got: {}".format(tok))
	raise Exception("Expected new expression, but got: {}".format(tok))

def parse_exp_un(tokens):
	if tokens and tokens[0] in ['-', '!']:
		tok = tokens.popleft()
		return Node(tok, parse_exp_un(tokens))
	return parse_exp_base(tokens)

def parse_exp_con(tokens):
	t = parse_exp_un(tokens)
	if tokens and tokens[0] == ':':
		tok = tokens.popleft()
		return Node(tok, t, parse_exp_con(tokens))
	return t
	
def tail_recursion(fn, ops, tokens):
	# fn is a function for the recursive descent
	# ops are the operators that should be matched on
	t = fn(tokens)
	while tokens and tokens[0] in ops:
		tok = tokens.popleft()
		t_right = fn(tokens)
		t = Node(tok, t, t_right)
	return t
	
# 'currying' so that we can continue to pass a function reference down
parse_exp_mult 	= partial(tail_recursion, parse_exp_con, ['*', '/', '%'])
parse_exp_add 	= partial(tail_recursion, parse_exp_mult, ['+', '-'])
parse_exp_cmp 	= partial(tail_recursion, parse_exp_add, ['<', '<=', '>', '>='])
parse_exp_eq 	= partial(tail_recursion, parse_exp_cmp, ['==','!='])
parse_exp_and 	= partial(tail_recursion, parse_exp_eq, ['&&'])
parse_exp_or 	= partial(tail_recursion, parse_exp_and, ['||'])
parse_exp 		= parse_exp_or

def build_tree(tokens):
	tokens = deque(tokens) # to allow popleft
	try:
		tree = parse_spl(tokens)
	except IndexError:
		raise Exception("Unfinished expression, but ran out of tokens.")
	if not tree:
		raise Exception("Unable to parse: program is empty?")
	if tokens:
		raise Exception("Done parsing, but there are still tokens remaining. Next token: {}".format(tokens[0]))
	return tree

def main():
	pass
	
if __name__ == '__main__':
	main()
	
	
# design choices:
# for tuples, the comma is overloaded as it also defines function calls, so cannot be the value of a node.
# To prevent this problem, we subsitute an '@' operator to imply tuples

# for statement concatenation (e.g. in scopes) we use a ';' as node value