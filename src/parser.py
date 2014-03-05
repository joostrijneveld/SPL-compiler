#! /usr/bin/env python

from collections import deque # superefficient popleft
from functools import partial

class Node:
	def __init__(self, val, *children):
		self.val = val
		self.children = children
		
	def __repr__(self, depth = 0):
		ret = ''
		for c in self.children[:len(self.children)/2]:
			ret += c.__repr__(depth + 1)
		ret += "\t"*depth+repr(self.val)+"\n"
		for c in self.children[len(self.children)/2:]:
			ret += c.__repr__(depth + 1)
		return ret

def remove_literal_token(tokens, literal):
	tok = tokens.popleft()
	if tok != literal:
		raise Exception("Expected '{}' but got: {}".format(literal, tok))
	
def parse_stmt(tokens):
	try:
		tok = tokens.popleft()
		if tok[0] == 'id':
			if tokens[0] == '(': # for ExpFunc
				result = parse_exp_func(tok, tokens)
			else: # for ExpField
				exp_field = parse_exp_field(tok, tokens)
				remove_literal_token(tokens, '=')
				result = Node('=', exp_field, parse_exp(tokens))
			remove_literal_token(tokens, ';')
			return result
		elif tok == 'if':
			remove_literal_token(tokens, '(')
			condition = parse_exp(tokens)
			remove_literal_token(tokens, ')')
			if_stmt = parse_stmt(tokens)
			if tokens and tokens[0] == 'else': # optional else
				tokens.popleft()
				return Node('if', condition, if_stmt, parse_stmt(tokens))
			return Node('if', condition, if_stmt)
		elif tok == 'while':
			remove_literal_token(tokens, '(')
			condition = parse_exp(tokens)
			remove_literal_token(tokens, ')')
			return Node('while', condition, parse_stmt(tokens))
		elif tok == 'return':
			if tokens[0] == ';':
				remove_literal_token(tokens, ';')
				return Node('return')
			result = parse_exp(tokens)
			remove_literal_token(tokens, ';')
			return Node('return', result)
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
	tokens.popleft() # pop off the '(' that was tested for in parse_exp_base
	t_right = parse_exp_args(tokens)
	remove_literal_token(tokens, ')')
	return Node('FN', t_left, t_right)

def parse_exp_base(tokens):
	# Parses the first expression from tokens and returns it as a parse tree
	try:
		tok = tokens.popleft()
		if tok[0] == 'id':
			if tokens[0] == '(': # for ExpFunc
				return parse_exp_func(tok, tokens)
			return parse_exp_field(tok, tokens)
		elif tok[0] in ['int', 'bool']:
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
					return Node('@', t_left, t_right)
				raise Exception("Expected ')', but got: {}".format(tok))
			elif tok == ')':
				if not t_right:
					return t_left
			raise Exception("Expected ')' or ',', but got: {}".format(tok))
		raise Exception("Expected new expression, but got: {}".format(tok))
	except IndexError:
		raise Exception("Unfinished expression, but ran out of tokens.")

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
parse_exp_args	= partial(tail_recursion, parse_exp, [','])

def build_tree(tokens):
	tokens = deque(tokens) # to allow popleft
	tree = parse_stmt(tokens)
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