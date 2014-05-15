#! /usr/bin/env python

import re, collections

LITERALS = [
    'True', 'False',
    'if', 'then', 'else', 'while', 'return', 'Void', 'Int', 'Bool', '[]',
    '!', '-', '+', '*', '/', '%', ':', '&&', '||',
    '==', '<', '>', '<=', '>=', '!=',
    ',', ';', '{', '}', '[', ']', '(', ')', '=',
    '.hd', '.tl', '.fst', '.snd']

TOKENTYPES = ['id','int'] + LITERALS

class Token(collections.namedtuple('TokenBase', ['line','col','type','val'])):
    def __repr__(self):
        return (self.type + ('['+str(self.val)+']')*(self.val is not None) +
                ' ['+ str(self.line) + ':' + str(self.col)+']')

class Position:
    def __init__(self):
        self.line = self.col = self.prevcol = 1
    
    def nextline(self):
        self.prevcol = self.col =  1
        self.line += 1
    
    def eval_tokpos(self):
        result, self.prevcol = self.prevcol, self.col
        return result
        
def handle_comments(f, blockcomment, p):
    if blockcomment:
        last_two = collections.deque(maxlen=2)
        while ''.join(last_two) != '*/':
            c = f.read(1)
            if not c:
                raise Exception("Unfinished comment. Reached end of file.")
            p.col += 1
            if c == '\n':
                p.nextline()
            last_two.append(c)
            # if ''.join(last_two) == '/*': # nested comments
                # handle_comments(f, True, p)
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
            if t in LITERALS and token == t or t == 'int' and token.isdigit():
                result = t
                break
        else:
            if re.match('^[a-z][a-z0-9_]*\Z', token, re.IGNORECASE):
                result = 'id'
            else:
                raise Exception("Unrecognised token: "+token)
    if result == 'id':
        tokens.append(Token(p.line, p.eval_tokpos(), result, token))
    elif result == 'int':
        tokens.append(Token(p.line, p.eval_tokpos(), result, int(token)))
    elif result in ['True', 'False']: #exceptional case for booleans
        tokens.append(Token(p.line, p.eval_tokpos(), 'bool', result == 'True'))
    else:
        tokens.append(Token(p.line, p.eval_tokpos(), result, None))
        
def scan_spl(fin):
    tokens = []
    p = Position()
    prevcandidates = candidates = list(TOKENTYPES)
    prevtoken = token = ''
    while True:
        c = fin.read(1)
        p.col += 1
        if not c:  # no more chars to read
            if token:
                complete_token(candidates, token, tokens, p)
            break
        elif not token and not c.strip():
            p.eval_tokpos()
            if c == '\n':
                p.nextline()
            continue  # no token, and the next char is whitespace => skip!
        token += c
        if token in ['//', '/*']:
            handle_comments(fin, token == '/*', p)
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
    
