#! /usr/bin/env python

import re

TOKENTYPES = ['id','int','op','punct', 'True', 'False', 'if', 'then',
'else', 'while', 'return', 'Void', 'Int', 'Bool', 'hd', 'tl', 'fst', 'snd']
OPERATORS = ['!', '-', '+','-', '*', '/', '%', '==',
		'<', '>', '<=', '>=', '!=', '&&', '||', ':']
PUNCTUATION = [',', ';', '{', '}', '[', ']', '(', ')', '=']
KEYWORDS = ['True', 'False', 'if', 'then', 'else',
			'while', 'return', 'Void', 'Int', 'Bool']
METHODS = ['hd', 'tl', 'fst', 'snd']

def handle_comments(f, blockcomment):
	if blockcomment:
		last_two = ''
		while last_two != '*/':
			c = f.read(1)
			last_two += c
			last_two = last_two[-2:]
	else:
		f.readline()

def update_candidates(candidates, token):
	for t in list(candidates):
		if t == 'id':
			if not re.match('^[a-z][a-z0-9_]*\Z', token, re.IGNORECASE):
				candidates.remove(t)
		if t == 'int':
			if not token.isdigit():
				candidates.remove(t)
		if t == 'op':
			if not any(x.startswith(token) for x in OPERATORS):
				candidates.remove(t)
		if t == 'punct':
			if token not in PUNCTUATION:
				candidates.remove(t)
		if t in KEYWORDS:
			if not t.startswith(token):
				candidates.remove(t)
		if t in METHODS:
			if not token[0] == '.' or not any(x.startswith(token[1:]) for x in METHODS):
				candidates.remove(t)

def complete_token(candidates, prevcandidates, token, prevtoken, tokens, f):
	if len(prevcandidates) == 1:
		t = prevcandidates[0]
		if t in ['id', 'op', 'punct']:
			tokens.append((t, prevtoken))
		elif t == 'int':
			tokens.append((t, int(prevtoken)))
		elif t in ['True', 'False']:
			tokens.append((t, prevtoken == 'True')) # to store the boolean value
		else:
			tokens.append((t, ))  # still add a tuple, for type consistency
	else: # so there were multiple previous candidates and we need to perform a tiebreak
		for t in list(prevcandidates):
			if t in KEYWORDS and prevtoken == t:
				# this is always the keyword, and not a prefix of an id - otherwise we would not be in len() = 0.
				tokens.append((t, ))
				break
			elif t == 'punct' and prevtoken in PUNCTUATION:
				# this case only exists when prevtoken is '=', since that overlaps with operator '=='
				# but now this operator is apparently no longer a candidate for token (since N = 0),
				# so it must be a punct '=' token
				tokens.append((t, prevtoken))
				break
			elif t == 'op' and prevtoken in OPERATORS:
				tokens.append((t, prevtoken))
				break
			elif t in METHODS and prevtoken[1:] == t:
				tokens.append((t, ))
				break
			elif t == 'int' and prevtoken.isdigit():
				tokens.append((t, int(prevtoken)))
				break
		# all that remains is an id-type (as we did not break in any of the if-statements)
		else:
			if re.match('^[a-z][a-z0-9_]*\Z', prevtoken, re.IGNORECASE):
				tokens.append(('id', prevtoken))
			else:
				raise Exception("Unrecognised token: "+prevtoken)

def scan_spl(fname):
	tokens = []
	with open(fname, 'r') as f:
		prevcandidates = candidates = list(TOKENTYPES)
		prevtoken = token = ''
		while True:
			c = f.read(1)
			token += c
			if len(token.strip()) == 0 and c:
				token = ''
				continue
			if not token and c == '':
				break
			if token in ['//', '/*']:
				handle_comments(f,token == '/*')
				token = ''
				candidates = list(TOKENTYPES)
			else:
				update_candidates(candidates, token)
				if len(candidates) == 0:
					complete_token(candidates, prevcandidates, token, prevtoken, tokens, f)
					token = token[-1].strip() 	# restart the next token with the remaining character
					candidates = list(TOKENTYPES) # and re-enable all candidates
				if c == '':
					complete_token(candidates, prevcandidates, token, prevtoken, tokens, f)
					token = ''
			# preparing for next iteration
			prevtoken, prevcandidates = token, list(candidates)
		print 'Tokens: ',tokens
		
def main():
	scan_spl('../test.spl')
	
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
