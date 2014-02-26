#! /usr/bin/env python

from collections import deque # superefficient popleft

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

def parse_t(tokens):
	# Parses the first term from tokens and returns it as a parse tree
	t = tokens.popleft()
	if t[0] in ['id', 'int']:
		return Node(None, t, None)
	raise Exception("Expected id or integer, but got: "+str(t))

def parse_expr(tokens):
	# E = T ((- | +) T)*
	t = parse_t(tokens)
	token = tokens[0]
	while token in ['-', '+'] and tokens:
		tokens.popleft()
		t2 = parse_t(tokens)
		t = Node(t, token, t2)
		if tokens:
			token = tokens[0]
	return t
	
def parse_tail_rec(parsefn, operators):
	pass
	
def build_tree(tokens):
	return parse_expr(deque(tokens))

def main():
	pass
	# t = Node(None, 5, None)
	# # print t
	# t2 = Node(None, 7, None)
	# t3 = Node(t2, 1, t)
	# t4 = Node(None, 4, t3)
	# print t4
	# print 'Tokens: ', scan_spl('../test.spl')
	
if __name__ == '__main__':
	main()