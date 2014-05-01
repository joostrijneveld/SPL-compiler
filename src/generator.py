
def generate_vardecl(tree, wab, tables):
	pass
	
def generate_fundecl(tree, wab, tables):
	pass

def generate_decls(tree, wab, tables):
	if not tree:
		return
	if tree.children[0].tok == 'FunDecl':
		pass
	if tree.children[0].tok == 'VarDecl':
		generate_vardecl(tree.children[0], wab, tables)
	generate_decls(tree.children[1], wab, tables)
	
def generate_ssm(tree, tables, fname):
	wab = dict() # address book
	generate_decls(tree, wab, tables)
	