#! /usr/bin/env python

import re
from collections import namedtuple, deque

LITERALS = [
    'True', 'False', 'Int', 'Bool', 'Char', 'Void', '[]',
    'if', 'then', 'else', 'while', 'return',
    '!', '-', '+', '*', '/', '%', ':', '&&', '||',
    '==', '<', '>', '<=', '>=', '!=',
    ',', ';', '{', '}', '[', ']', '(', ')', '=',
    '.hd', '.tl', '.fst', '.snd']

TOKENTYPES = ['id', 'int', 'char'] + LITERALS


class Token(namedtuple('TokenBase', ['line', 'col', 'type', 'val'])):
    def __repr__(self):
        return (self.type + ('['+str(self.val)+']')*(self.val is not None) +
               ' [' + str(self.line) + ':' + str(self.col) + ']')


class Position:
    def __init__(self):
        self.line = self.col = self.prevcol = 1

    def nextline(self):
        self.prevcol = self.col = 1
        self.line += 1

    def eval_tokpos(self):
        result, self.prevcol = self.prevcol, self.col
        return result


def handle_comments(f, blockcomment, p):
    if blockcomment:
        last_two = deque(maxlen=2)
        while ''.join(last_two) != '*/':
            c = f.read(1)
            if not c:
                raise Exception("Unfinished comment. Reached end of file.")
            p.col += 1
            if c == '\n':
                p.nextline()
            last_two.append(c)
            # if ''.join(last_two) == '/*': # nested comments
            #     handle_comments(f, True, p)
    else:
        f.readline()
        p.nextline()


def preprocess_string(f, p):
    chararray = []
    c = ''
    while c != '"':
        c = f.read(1)
        if not c:
            raise Exception("Unfinished string. Reached end of file.")
        p.col += 1
        if c == '\n':
            p.nextline()
        if c != '"':
            chararray.append(Token(p.line, p.eval_tokpos(), 'char', c))
            chararray.append(Token(p.line, p.eval_tokpos(), ':', None))
    chararray.append(Token(p.line, p.eval_tokpos(), '[]', None))
    return chararray


def update_candidates(candidates, token):
    for t in list(candidates):
        if t == 'id':
            if not re.match('^[a-z][a-z0-9_]*\Z', token, re.IGNORECASE):
                candidates.remove(t)
        elif t == 'char':
            if token[0] != "'" or len(token) > 3 or len(token) == 3 and token[2] != "'":
                candidates.remove(t)
        elif t == 'int':
            if not token.isdigit():
                candidates.remove(t)
        else:
            if not t.startswith(token):
                candidates.remove(t)


def complete_token(candidates, token, tokens, p):
    if token in ['True', 'False']:
        tokens.append(Token(p.line, p.eval_tokpos(), 'bool', token == 'True'))
    elif token in LITERALS:
        tokens.append(Token(p.line, p.eval_tokpos(), token, None))
    elif re.match('^[a-z][a-z0-9_]*\Z', token, re.IGNORECASE):
        tokens.append(Token(p.line, p.eval_tokpos(), 'id', token))
    elif len(token) == 3 and token[0] == token[-1] == "'":
        tokens.append(Token(p.line, p.eval_tokpos(), 'char', token[1:-1]))
    elif token.isdigit():
        tokens.append(Token(p.line, p.eval_tokpos(), 'int', int(token)))
    else:
        raise Exception("Unrecognised token: "+token)


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
        elif token in ['"']:
            p.eval_tokpos()  # to correct for the opening quote
            tokens += preprocess_string(fin, p)
            token = ''
            candidates = list(TOKENTYPES)
        else:
            update_candidates(candidates, token)
            if not candidates:  # so if the current token is not valid
                complete_token(prevcandidates, prevtoken, tokens, p)
                if token[-1] == '\n':
                    p.nextline()
                # start next token with invalidating character
                token = token[-1].strip()
                candidates = list(TOKENTYPES)  # re-instantiate all candidates
        # prepare for next iteration
        prevtoken, prevcandidates = token, list(candidates)
    return tokens
