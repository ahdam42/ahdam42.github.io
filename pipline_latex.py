import pylatexenc.latexwalker as pylxt



path2latex = 'data/latex/ICPRsubmission.tex'

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
print(env.len)

# print(nodes_upd)
# print(type(nodes_upd[0]))
# print(len(nodes_upd))