#! /usr/bin/env python

import re

LITERALS = [
    'True', 'False',
    'if', 'then', 'else', 'while', 'return', 'Void', 'Int', 'Bool', '[]',
    '!', '-', '+', '*', '/', '%', ':', '&&', '||',
    '==', '<', '>', '<=', '>=', '!=',
    ',', ';', '{', '}', '[', ']', '(', ')', '=',
    '.hd', '.tl', '.fst', '.snd']

TOKENTYPES = ['id','int'] + LITERALS

class Token:
	def __init__(self, line, col, type, val=None):
		self.line = line
		self.col = col
		self.type = type
		self.val = val
		
	def __repr__(self):
		return self.type + ('['+str(self.val)+']' if self.val else '') +' ' \
				+ str(self.line) + ':' + str(self.col)

class Position:
	def __init__(self):
		self.line = self.col = self.prevcol = 1
	
	def nextline(self):
		self.prevcol = 1
		self.col = 1
		self.line += 1
	
	def tokpos(self):
		result, self.prevcol = self.prevcol, self.col
		return result
		
def handle_comments(f, blockcomment, p):
	if blockcomment:
		last_two = ''
		while last_two != '*/':
			c = f.read(1)
			p.col += 1
			if c == '\n':
				p.nextline()
			last_two += c
			last_two = last_two[-2:]
	else:
		f.readline()
		p.nextline()

def update_candidates(candidates, token):
	for t in list(candidates):
		if t == 'id':
			if not re.match('^[a-z][a-z0-9_]*\Z', token, re.IGNORECASE):
				candidates.remove(t)
		elif t == 'int':
			if not token.isdigit():
				candidates.remove(t)
		else:
			if not t.startswith(token):
				candidates.remove(t)
				
def complete_token(candidates, token, tokens, p):
	if len(candidates) == 1:
		result = candidates[0]
	else:
		for t in list(candidates):
			if (t in LITERALS and token == t) or (t == 'int' and token.isdigit()):
				result = t
				break
		else:
			if re.match('^[a-z][a-z0-9_]*\Z', token, re.IGNORECASE):
				result = 'id'
			else:
				raise Exception("Unrecognised token: "+token)
	if result == 'id':
		tokens.append(Token(p.line, p.tokpos(), result, token))
	elif result == 'int':
		tokens.append(Token(p.line, p.tokpos(), result, int(token)))
	elif result in ['True', 'False']: #exceptional case for booleans
		tokens.append(Token(p.line, p.tokpos(), 'bool', result == 'True'))
	else:
		tokens.append(Token(p.line, p.tokpos(), result))
		
def scan_spl(fname):
	tokens = []
	p = Position()
	with open(fname, 'r') as f:
		prevcandidates = candidates = list(TOKENTYPES)
		prevtoken = token = ''
		while True:
			c = f.read(1)
			p.col += 1
			if not c:  # no more chars to read
				if token:
					complete_token(candidates, token, tokens, p)
				break
			elif not token and not c.strip():
				p.tokpos()
				if c == '\n':
					p.nextline()
				continue  # no token, and the next char is whitespace => skip!
			token += c
			if token in ['//', '/*']:
				handle_comments(f, token == '/*', p)
				token = ''
				candidates = list(TOKENTYPES)
			else:
				update_candidates(candidates, token)
				if not candidates: # so if the current token is not valid
					complete_token(prevcandidates, prevtoken, tokens, p)
					if token[-1] == '\n':
						p.nextline()
					token = token[-1].strip()  # start the next token with the invalidating character
					candidates = list(TOKENTYPES) # and re-instantiate all candidates
			# prepare for next iteration
			prevtoken, prevcandidates = token, list(candidates)
	return tokens
		
def main():
	print 'Tokens: ', scan_spl('../test.spl')
	
if __name__ == '__main__':
	main()
	
	
# Test en werkt: Int a.hd() = 5;


# Truee
# 
# true/then  (of id)

# 


# int i = 5;
# <id, 'int'>, (str, 'i'), (str, =), (int, 5)

# tokens types:

# id 			alpha ('_' | alphanum)*
# int 			['-'] digit+
# Op1			!, -
# Op2			+ - * / % == < > <= >= != && || :
# comma
# true
# false
# if
# then
# else
# while
# return
# Void
# Int
# Bool
# hd
# tl
# fst
# snd
# {, }, [, ], (, )
# =
# ;
# design choices: ids mogen geen keywords zijn
# dot kan weg want hd tl etc doen we gelijk in 1x als token
# we voegen de comma, brackets, equality en semicolon allemaal in het 'punct'-token samen voor leesbare code

# keuze: we maken 1 'op'-token waar ook meteen de min en de ! in zitten. we zoeken daarna wel uit of het op1 of op2 is

# we houden een ljistje bij van kandidaten-tokens die het nog kunnen zijn
# als het lijstje na een ronde 1 element bevat is het sowieso deze, maar gaan we door tot 'ie niet meer kan
# als het lijstje na een ronde >=2 elementen bevat moet je nog een keer
# als het lijstje na een ronde 0 elementen bevat moet je het vorige lijstje pakken en een tiebreak doen


# foo.
# hd

# <id, foo> <hd> 
