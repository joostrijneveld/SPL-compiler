#! /usr/bin/env python

TOKENTYPES = ['id','int','op1','op2','punct', 'True', 'False', 'if', 'then',
'else', 'while', 'return', 'Void', 'Int', 'Bool', 'hd', 'tl', 'fst', 'snd']

TOKENTYPES = ['id','op1','punct', 'True', 'False', 'if', 'then',
'else', 'while', 'return', 'Void', 'Int', 'Bool']

def scan_spl(fname):
	tokens = []
	with open(fname, 'r') as f:
		prevcandidates = candidates = list(TOKENTYPES)
		prevtoken = token = ''
		while True:
			c = f.read(1)  # do-while hack
			token += c
			for t in list(candidates):
				if t == 'id':
					if not (token[0].isalpha() and token[1:]):
						 #alpha ('_' | alphanum)
				if t == 'int':
					pass
				if t == 'op1':
					if token not in ['!', '-']:
						candidates.remove(t)
				if t == 'op2':
					pass
				if t == 'punct':
					if token not in [',', ';', '{', '}', '[', ']', '(', ')', '=']:
						candidates.remove(t)
				if t in ['True', 'False', 'if', 'then', 'else',
						 'while', 'return', 'Void', 'Int', 'Bool']:
					if not t.startswith(token):
						candidates.remove(t)
				if t == 'hd':
					pass
				if t == 'tl':
					pass
				if t == 'fst':
					pass
				if t == 'snd':
					pass
			print candidates
			if len(candidates) == 0 or c == '': # c = '' only at the end of the file
				if len(prevcandidates) == 1:
					t = candidates[0]
					if t in ['id', 'op1', 'op2', 'punct']:
						tokens.append((candidates[0], token))
					elif t == 'int':
						tokens.append((t, int(token)))
					elif t in ['True', 'False']:
						tokens.append((t, token == 'True'))
					else:
						tokens.append((t, ))  # still add a tuple, for type consistency
				else: # so there were multiple previous candidates and we need to perform a tiebreak
					for t in list(prevcandidates):
						if t in ['True', 'False', 'if', 'then', 'else',
							 'while', 'return', 'Void', 'Int', 'Bool']:
							# this is always the keyword, and not a prefix of an id - otherwise we would not be in len() = 0.
							if prevtoken == t:
								tokens.append((t, ))
								break
						elif t == 'punct':
							# this case only exists when prevtoken is '=', since that overlaps with op2 '=='
							# but now op2 is no longer a candidate for token, so it must be an op1 '=' token
							tokens.append(('punct', prevtoken))
							break
						# integers cannot be completed, otherwise it would not be in len() = 0 (since no other token matched it previously)
						# so integers cannot exist in a len() = 0 case.
					else: 
						# all that remains is an id-type this time (as we did not break in any of the if-statements)
						tokens.append(('id', prevtoken))
				token = ''
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

# we houden een ljistje bij van kandidaten-tokens die het nog kunnen zijn
# als het lijstje na een ronde 1 element bevat is het sowieso deze, maar gaan we door tot 'ie niet meer kan
# als het lijstje na een ronde >=2 elementen bevat moet je nog een keer
# als het lijstje na een ronde 0 elementen bevat moet je het vorige lijstje pakken en een tiebreak doen


# foo.
# hd

# <id, foo> <hd> 
