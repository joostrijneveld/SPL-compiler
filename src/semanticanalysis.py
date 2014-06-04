#! /usr/bin/env python

import sys
from collections import namedtuple
from functools import partial
from scanner import Token  # required to add explicit return to Voids in AST
from parser import Node

Symbol = namedtuple('Symbol',
                    ['line', 'col', 'type', 'argtypes', 'glob', 'tree'])


class Type(object):
    def __init__(self, value):
        self.value = value

    @staticmethod
    def from_node(tree):  # tree is a Type-node
        if tree.tok.type in ['Bool', 'Int', 'Void', 'Char']:
            return Type(tree.tok.type)
        elif tree.tok.type == 'id':
            return Type(tree.tok.val)
        elif tree.tok.type == ',':
            return Type((Type.from_node(tree.children[0]),
                        Type.from_node(tree.children[1])))
        elif tree.tok.type == '[':
            return Type([Type.from_node(tree.children[0])])

    def __repr__(self):
        return repr(self.value)
        
    def unify(self, other):
        ''' attempts to unify non-generic types (necessary for empty lists)
            return value None means no unification could be found '''
        if type(self.value) is tuple and type(other.value) is tuple:
            left = self.value[0].unify(other.value[0])
            right = self.value[1].unify(other.value[1])
            if left is None or right is None:
                return None
            return Type((left, right))
        if type(self.value) is list and type(other.value) is list:
            result = self.value[0].unify(other.value[0])
            if result is None:
                return None
            return Type([result])
        if type(self.value) is str and type(other.value) is str:
            if self.value == other.value:
                return self
            return None
        if self.value is None:
            return other
        if other.value is None:
            return self
        return None


def print_symboltables(symtabs):
    for fname, symboltable in symtabs.items():
        if not symboltable:
            continue
        print("{:=^62}".format(" {} ".format(fname)))
        print("{0: <12} {1: <15} {2: <15} {3: <20}"
              .format('Position', 'Name', 'Type', 'Argtypes'))
        print('-'*62)
        for k, v in symboltable.items():
            argvstring = ", ".join(map(str, v.argtypes)) if v.argtypes is not None else ""
            print("{: <12} {: <15} {!s: <15} {: <20}"
                  .format("{0.line}:{0.col}".format(v), k, v.type, argvstring))
        print('='*62)


def find_argtypes(tree):
    ''' expects a tree with an arg-node (',') as root '''
    if not tree:
        return []
    return [Type.from_node(tree.children[0])] + find_argtypes(tree.children[2])


def update_symtab(symtab, tok, t, argtypes, glob, tree=None):
    if tok.val in symtab:
        oldsym = symtab[tok.val]
        if oldsym.glob and not glob:
            sys.stderr.write("[Line {}:{}] Warning: redefinition of global {}\n"
                             "[Line {}:{}] Previous definition was here\n"
                             .format(tok.line, tok.col, tok.val,
                                     oldsym.line, oldsym.col))
        else:
            raise Exception("[Line {}:{}] Redefinition of {}\n"
                            "[Line {}:{}] Previous definition was here"
                            .format(tok.line, tok.col,
                                    tok.val, oldsym.line, oldsym.col))
    symtab.update({tok.val: Symbol(tok.line, tok.col, t, argtypes, glob, tree)})


def create_table(tree, symtab, glob, vardecls):
    ''' expects a tree with a Decl-node as root '''
    if not tree:
        return symtab
    t = Type.from_node(tree.children[0].children[0])
    sym = tree.children[0].children[1].tok
    if tree.children[0].tok == 'FunDecl' and not vardecls:
        argtypes = find_argtypes(tree.children[0].children[2])
        update_symtab(symtab, sym, t, argtypes, glob, tree=tree.children[0])
    if tree.children[0].tok == 'VarDecl' and vardecls:
        check_vardecl(tree.children[0], symtab)
        update_symtab(symtab, sym, t, None, glob)
    return create_table(tree.children[1], symtab, glob, vardecls)


def create_argtable(tree, symtab):
    ''' expects a tree with an arg-node (',') as root '''
    if not tree:
        return symtab
    t = Type.from_node(tree.children[0])
    sym = tree.children[1].tok
    update_symtab(symtab, sym, t, None, False)
    return create_argtable(tree.children[2], symtab)


def type_id(tree, symtab):
    if tree.tok.val not in symtab:
        raise Exception("[Line {}:{}] Found id {}, but it has not been defined"
                        .format(tree.tok.line, tree.tok.col, tree.tok.val))
    return symtab[tree.tok.val].type


def type_exp_base(tree, symtab):
    if tree.tok.type == 'int':
        return Type('Int')
    elif tree.tok.type == 'bool':
        return Type('Bool')
    elif tree.tok.type == 'char':
        return Type('Char')
    elif tree.tok.type == '[]':
        return Type([Type(None)])
    elif tree.tok.type == 'FunCall':
        t = type_expfunc(tree, symtab)  # includes existence-check
        gentab = check_funcall(tree, symtab)
        return apply_gentab(tree, t, gentab)
    elif tree.tok.type == ',':
        return Type((type_exp(tree.children[0], symtab),
                    type_exp(tree.children[1], symtab)))
    else:
        return type_exp_field(tree, symtab)


def type_op(fn, in_types, out_type, ops, tree, symtab):
    if tree.tok.type in ops:
        rev_types = map(partial(type_exp, symtab=symtab), tree.children)
        gentab = dict()
        if not all(apply_generics(e, r, gentab) for e, r in zip(in_types, rev_types)):
            raise Exception("[Line {}:{}] Incompatible types for operator '{}'\n"
                            "  Types expected: {}\n"
                            "  Types found: {}"
                            .format(tree.tok.line, tree.tok.col, tree.tok.type,
                                    ', '.join(map(str, in_types)),
                                    ', '.join(map(str, rev_types))))
        return apply_gentab(tree, out_type, gentab)
    return fn(tree, symtab)

type_exp_hd = partial(type_op, type_id,
                      [Type([Type('t')])], Type('t'), ['.hd'])
type_exp_tl = partial(type_op, type_exp_hd,
                      [Type([Type('t')])], Type([Type('t')]), ['.tl'])
type_exp_fst = partial(type_op, type_exp_tl,
                       [Type((Type('a'), Type('b')))], Type('a'), ['.fst'])
type_exp_snd = partial(type_op, type_exp_fst,
                       [Type((Type('a'), Type('b')))], Type('b'), ['.snd'])
type_exp_field = type_exp_snd

type_exp_unint = partial(type_op, type_exp_base,
                         [Type('Int')], Type('Int'), ['-'])
type_exp_unbool = partial(type_op, type_exp_unint,
                          [Type('Bool')], Type('Bool'), ['!'])
type_exp_con = partial(type_op, type_exp_unbool,
                       [Type('t'), Type([Type('t')])], Type([Type('t')]), [':'])
type_exp_math = partial(type_op, type_exp_con,
                        [Type('Int'), Type('Int')], Type('Int'), ['+', '-', '*', '/', '%'])
type_exp_cmp = partial(type_op, type_exp_math,
                       [Type('Int'), Type('Int')], Type('Bool'), ['<', '<=', '>', '>='])
type_exp_eq = partial(type_op, type_exp_cmp,
                      [Type('t'), Type('t')], Type('Bool'), ['==', '!='])
type_exp_andor = partial(type_op, type_exp_eq,
                         [Type('Bool'), Type('Bool')], Type('Bool'), ['&&', '||'])
type_exp = type_exp_andor


def type_expargs(tree, symtab):
    ''' expects a tree with an arg-node (',') as root '''
    if not tree:
        return []
    return ([type_exp(tree.children[0], symtab)]
            + type_expargs(tree.children[1], symtab))


def type_expfunc(tree, symtab):
    return type_id(tree.children[0], symtab)


def apply_gentab(tree, t, gentab):
    '''replaces generics that occur in t with their literal type from gentab'''
    if t.value in ['Int', 'Bool', 'Void', 'Char']:
        return t
    if type(t.value) is str:
        return gentab[t.value]  # validated that it is always in the gentab
    if type(t.value) is tuple:
        return Type((apply_gentab(tree, t.value[0], gentab),
                    apply_gentab(tree, t.value[1], gentab)))
    if type(t.value) is list:
        return Type([apply_gentab(tree, t.value[0], gentab)])


def apply_generics(gen_type, lit_type, gentab):
    ''' checks if gen_type can be applied to lit_type, updates gentab '''
    if gen_type.value in ['Int', 'Bool', 'Char']:
        return gen_type.unify(lit_type) is not None
    if type(gen_type.value) is str:
        if gen_type.value in gentab:
            result = gentab[gen_type.value].unify(lit_type)
            if not result:
                return False
            gentab[gen_type.value] = result
        else:
            gentab[gen_type.value] = lit_type
        return True
    if type(gen_type.value) is tuple and type(lit_type.value) is tuple:
        return (apply_generics(gen_type.value[0], lit_type.value[0], gentab)
                and apply_generics(gen_type.value[1], lit_type.value[1], gentab))
    if type(gen_type.value) is list and type(lit_type.value) is list:
        return apply_generics(gen_type.value[0], lit_type.value[0], gentab)
    return False


def check_funcall(tree, symtab):
    fname = tree.children[0].tok.val
    funsym = symtab[fname]
    if funsym.argtypes is None:
        raise Exception("[Line {}:{}] '{}' is a variable, not a function."
                        .format(tree.tok.line, tree.tok.col, fname))
    received = type_expargs(tree.children[1], symtab)
    if not len(funsym.argtypes) == len(received):
        raise Exception("[Line {}:{}] Incompatible number of arguments "
                        "for function '{}'.\n"
                        "  Arguments expected: {}\n"
                        "  Arguments found: {}"
                        .format(tree.tok.line, tree.tok.col, fname,
                                len(funsym.argtypes), len(received)))
    gentab = dict()
    if (not all(apply_generics(e, r, gentab)
    for e, r in zip(funsym.argtypes, received))):
        raise Exception("[Line {}:{}] Incompatible argument types "
                        "for function '{}'.\n"
                        "  Types expected: {}\n"
                        "  Types found: {}"
                        .format(tree.tok.line, tree.tok.col, fname,
                                ', '.join(map(str, funsym.argtypes)),
                                ', '.join(map(str, received))))
    globsymtab = {k: sym for k, sym in symtab.items() if sym.glob}
    usedfns.add(fname)
    check_functionbinding(funsym.tree, globsymtab, fname)
    return gentab


def check_stmt(tree, symtab, rettype):
    ''' expects a tree with a statement node as root '''
    if tree.tok.type == 'Scope':
        return check_stmts(tree.children[0], symtab, rettype)
    elif tree.tok.type == 'FunCall':
        type_expfunc(tree, symtab)  # needed to confirm the id definition
        check_funcall(tree, symtab)
    elif tree.tok.type == 'if' or tree.tok.type == 'while':
        condition = type_exp(tree.children[0], symtab)
        if condition.unify(Type('Bool')) is None:
            raise Exception("[Line {}:{}] Incompatible condition type\n"
                            "  Expected expression of type: Bool\n"
                            "  But got value of type: {}"
                            .format(tree.tok.line, tree.tok.col, condition))
        returned = False
        if tree.tok.type == 'if' and tree.children[2]:  # for 'else'-clause
            returned = check_stmt(tree.children[2], symtab, rettype)
        return check_stmt(tree.children[1], symtab, rettype) and returned
    elif tree.tok.type == '=':
        fieldtype = type_exp_field(tree.children[0], symtab)
        exptype = type_exp(tree.children[1], symtab)
        if fieldtype.unify(exptype) is None:
            raise Exception("[Line {}:{}] Invalid assignment for id {}\n"
                            "  Expected expression of type: {}\n"
                            "  But got value of type: {}"
                            .format(tree.tok.line, tree.tok.col,
                                    tree.children[0].tok.val, fieldtype, exptype))
    elif tree.tok.type == 'return':
        if not tree.children[0]:
            exptype = Type('Void')
        else:
            exptype = type_exp(tree.children[0], symtab)
        if rettype.unify(exptype) is None:
            raise Exception("[Line {}:{}] Invalid return type\n"
                            "  Function is of type: {}\n"
                            "  But returns value of type: {}"
                            .format(tree.tok.line, tree.tok.col,
                                    rettype, exptype))
        return True


def check_stmts(tree, symtab, rettype, outerscope=False):
    if tree:
        returned = check_stmt(tree.children[0], symtab, rettype)
        if returned and tree.children[1] is not None:
            raise Exception("[Line {}:{}] Unreachable code detected\n"
                            "  If this is intentional, enclose it in comments"
                            .format(tree.children[1].children[0].tok.line,
                                    tree.children[1].children[0].tok.col))
        if all([not returned, not tree.children[1],
                outerscope, rettype.unify(Type('Void'))]):
            returnnode = Node(Token(0, 0, 'return', None), None)
            tree.children[1] = Node(';', returnnode, None)
        return returned or check_stmts(tree.children[1], symtab, rettype, outerscope)


def check_vardecl(tree, symtab):
    vartype = Type.from_node(tree.children[0])
    exptype = type_exp(tree.children[2], symtab)
    if vartype.unify(exptype) is None:
        raise Exception("[Line {}:{}] Invalid assignment for id {}\n"
                        "  Expected expression of type: {}\n"
                        "  But got value of type: {}"
                        .format(tree.children[1].tok.line,
                                tree.children[1].tok.col, tree.children[1].tok.val,
                                vartype, exptype))


def list_generics(t):
    if t.value in ['Int', 'Bool', 'Void', 'Char']:
        return set()
    if type(t.value) is str:
        return set([t.value])
    if type(t.value) is tuple:
        return list_generics(t.value[0]) | list_generics(t.value[1])
    if type(t.value) is list:
        return list_generics(t.value[0])


def check_rettype_binding(tree, rettype, symtab):
    '''checks if all generics that occur in rettype are bound by the symtab'''
    boundgenerics = set()
    for key, s in symtab.items():
        if s.argtypes is None:
            boundgenerics |= list_generics(s.type)
    unbound = list_generics(rettype) - boundgenerics
    if len(unbound) > 0:
        raise Exception("[Line {}:{}] Generic return type{} '{}' of function "
                        "{} not bound by arguments, so cannot be resolved."
                        .format(tree.children[1].tok.line,
                                tree.children[1].tok.col,
                                's' if len(unbound) > 1 else '',
                                ', '.join(str(t) for t in sorted(unbound)),
                                tree.children[1].tok.val))


def check_functionbinding(tree, globalsymtab, fname):
    if fname in symtabs:
        return symtabs[fname]  # to prevent infinite left-recursion via funcall
    rettype = globalsymtab[tree.children[1].tok.val].type
    symtabs[fname] = create_argtable(tree.children[2], globalsymtab.copy())
    check_rettype_binding(tree, rettype, symtabs[fname])
    symtabs[fname] = create_table(tree.children[3], symtabs[fname], False, True)
    returned = check_stmts(tree.children[4], symtabs[fname], rettype, True)
    if not returned and rettype.unify(Type('Void')) is None:
        raise Exception("[Line {}:{}] Missing return statement "
                        "in a non-Void function"
                        .format(tree.children[1].tok.line,
                                tree.children[1].tok.col))


def check_uncalled_functions(tree, globalsymtab):
    if not tree:
        return
    if tree.children[0].tok == 'FunDecl':
        fname = tree.children[0].children[1].tok.val
        check_functionbinding(tree.children[0], globalsymtab, fname)
    check_uncalled_functions(tree.children[1], globalsymtab)

symtabs = None
usedfns = set()

def check_binding(tree, globalsymtab=dict()):
    global symtabs
    symtabs = {k: None for k in globalsymtab}  # assume predef. functions are ok
    symtabs['_glob'] = dict(globalsymtab)
    symtabs['_glob'].update(create_table(tree, symtabs['_glob'], True, False))
    symtabs['_glob'].update(create_table(tree, symtabs['_glob'], True, True))
    usedsyms = {k: v for k, v in symtabs['_glob'].items()
        if k in usedfns or v.argtypes is None}
    check_uncalled_functions(tree, symtabs['_glob'])
    print_symboltables(symtabs)
    return usedsyms
