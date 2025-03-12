import pylatexenc.latexwalker as pylxt

import src.DAO.DataObj as DataObj

def get_title(node):
    if type(node) is pylxt.LatexMacroNode:
        node: pylxt.LatexMacroNode

        if node.macroname == 'title':
            return node.nodeargd.argnlist[0].nodelist[0].chars
    else:
        return ''

def get_author(node):
    if type(node) is pylxt.LatexMacroNode:
        node: pylxt.LatexMacroNode

        if node.macroname == 'author':
            for i in node.nodeargd.argnlist[0].nodelist:
                print(i)
            print(node.nodeargd.argnlist)
            return node.nodeargd.argnlist[0].nodelist[0].chars
    else:
        return ''


path2latex = 'arx.tex'

with open(path2latex, 'r') as f:
    latex_txt = f.read()

# Создание экземпляра LatexWalker
walker = pylxt.LatexWalker(latex_txt)

# Парсинг LaTeX-кода
nodes, _, _ = walker.get_latex_nodes()

nodes_upd = []
env = None
for nd in nodes:
    if type(nd) is pylxt.LatexEnvironmentNode:
        env = nd
    elif type(nd) not in [pylxt.LatexCommentNode, pylxt.LatexCommentNode, pylxt.LatexCharsNode]:
       nodes_upd.append(nd)

env: pylxt.LatexEnvironmentNode


flag_title = False
flag_author = False
for nd in env.nodelist:
    if not flag_title:
        title = get_title(nd)

        if title:
            flag_title = True

    if not flag_author:
        author = get_author(nd)

        if author:
            flag_author = True


print(title)
print(author)

# print(nodes_upd)
# print(type(nodes_upd[0]))
# print(len(nodes_upd))