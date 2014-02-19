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

def scan_spl(fname):
	tokens = []
	with open(fname, 'r') as f:
		prevcandidates = candidates = list(TOKENTYPES)
		prevtoken = token = ''
		while True:
			c = f.read(1)
			token += c
			if len(token.strip()) == 0:
				token = ''
				continue
			for t in list(candidates):
				if t == 'id':
					if not re.match('^[a-z][a-z0-9_]*\Z', token, re.IGNORECASE):
						candidates.remove(t)
				if t == 'int':
					if not token.isdigit():
						candidates.remove(t)
				if t == 'op':
					if not any(x.startswith(token)
							for x in OPERATORS):
						candidates.remove(t)
				if t == 'punct':
					if token not in PUNCTUATION:
						candidates.remove(t)
				if t in KEYWORDS:
					if not t.startswith(token):
						candidates.remove(t)
				if t in METHODS:
					if token[0] == '.':
						if not any(x.startswith(token[1:]) for x in METHODS):
							candidates.remove(t)
					else:
						candidates.remove(t)
			print "Candidates:" , candidates, "Token:", token
			if len(candidates) == 0  or c == '': # c = '' only at the end of the file
				if len(prevcandidates) == 1:
					t = prevcandidates[0]
					if t in ['id', 'op', 'punct']:
						tokens.append((t, prevtoken))
					elif t == 'int':
						tokens.append((t, int(prevtoken)))
					elif t in ['True', 'False']:
						tokens.append((t, prevtoken == 'True'))
					else:
						tokens.append((t, ))  # still add a tuple, for type consistency
				else: # so there were multiple previous candidates and we need to perform a tiebreak
					for t in list(prevcandidates):
						if t in KEYWORDS:
							# this is always the keyword, and not a prefix of an id - otherwise we would not be in len() = 0.
							if prevtoken == t:
								tokens.append((t, ))
								break
						elif t == 'punct' and prevtoken in PUNCTUATION:
							# this reason is no longer necessary since we now strict-check
							# this case only exists when prevtoken is '=', since that overlaps with operator '=='
							# but now this operator is apparently no longer a candidate for token (since N = 0),
							# so it must be a punct '=' token
							tokens.append(('punct', prevtoken))
							break
						elif t == 'op' and prevtoken in OPERATORS:
							tokens.append(('punct', prevtoken))
							break
						elif t in METHODS:
							if prevtoken[1:] == t:
								tokens.append((t, ))
								break
						# integers cannot be completed, otherwise it would not be in len() = 0 (since no other token matched it previously)
						# so integers cannot exist in a len() = 0 case.  -> NOT TRUE: Int a = [4,5];
					else: 
						# all that remains is an id-type this time (as we did not break in any of the if-statements)
						tokens.append(('id', prevtoken))
				token = token[-1].strip() 	# restart the next token with the remaining character
				candidates = list(TOKENTYPES)
			if c == '':
				break
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
