#! /usr/bin/env python

from collections import deque # superefficient popleft
from functools import partial

class Node:
	def __init__(self, left, val, right):
		self.left = left
		self.right = right
		self.val = val
		
	def __repr__(self, depth = 0):
		ret = ""
		if self.left:
			ret += self.left.__repr__(depth + 1)
		ret += "\t"*depth+repr(self.val)+"\n"
		if self.right:
			ret += self.right.__repr__(depth + 1)
		return ret

def build_tree(tokens):
	
	def parse_exp_field(id_tok, tokens):
		t = Node(None, id_tok, None)
		while tokens and tokens[0] in ['.hd', '.tl', '.fst', '.snd']:
			tok = tokens.popleft()
			t = Node(t, tok, None)
		return t
	
	def parse_exp_func(id_tok, tokens):
		t_left = Node(None, id_tok, None)
		tokens.popleft() # pop off the '(' that was tested for in parse_exp_base
		t_right = parse_exp_args(tokens)
		if tokens.popleft() != ')': # pop off the ')'
			raise Exception("Expected ')' but got: "+str(tok))
		return Node(t_left, 'FN', t_right)
	
	def parse_exp_base(tokens):
		# Parses the first term from tokens and returns it as a parse tree
		try:
			tok = tokens.popleft()
			if tok[0] == 'id':
				if tokens[0] == '(': # for tfunc
					return parse_exp_func(tok, tokens)
				return parse_exp_field(tok, tokens)
			elif tok[0] in ['int', 'bool']:
				return Node(None, tok, None)
			elif tok == '[':
				tok = tokens.popleft()
				if tok == ']':
					return Node(None,'[]', None)
				raise Exception("Expected ']', but got: "+str(tok))
			elif tok == '(':
				t_left = parse_exp(tokens)
				t_right = None
				tok = tokens.popleft()
				if tok == ',': # we're dealing with a tuple
					t_right = parse_exp(tokens)
					tok = tokens.popleft()
					if tok == ')':
						return Node(t_left, '@', t_right)
					raise Exception("Expected ')', but got: "+str(tok))
				elif tok == ')':
					if not t_right:
						return t_left
				raise Exception("Expected ')' or ',', but got: "+str(tok))
			raise Exception("Expected new term, but got: "+str(tok))
		except IndexError:
			raise Exception("Unfinished term, but ran out of tokens.")

	def parse_exp_un(tokens):
		if tokens and tokens[0] in ['-', '!']:
			tok = tokens.popleft()
			return Node(parse_exp_un(tokens), tok, None)
		return parse_exp_base(tokens)

	def parse_exp_con(tokens):
		t = parse_exp_un(tokens)
		if tokens and tokens[0] == ':':
			tok = tokens.popleft()
			return Node(t, tok, parse_exp_con(tokens))
		return t

	def tail_recursion(fn, ops, tokens):
		# fn is a function for the recursive descent
		# ops are the operators that should be matched on
		t = fn(tokens)
		while tokens and tokens[0] in ops:
			tok = tokens.popleft()
			t_right = fn(tokens)
			t = Node(t, tok, t_right)
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
	
	tokens = deque(tokens) # to allow popleft
	tree = parse_exp(tokens)
	if tokens:
		raise Exception("Done parsing, but there are still tokens remaining. Next token: "+str(tokens[0]))
	return tree

def main():
	pass
	
if __name__ == '__main__':
	main()
	
	
# design choices:
# for tuples, the comma is overloaded as it also defines function calls, so cannot be the value of a node.
# To prevent this problem, we subsitute an '@' operator to imply tuples