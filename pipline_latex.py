import pylatexenc.latexwalker as pylxt
import re
from typing import Union

import src.DAO.DataObj as DataObj


def lock_search(func):
    """
    After walk through the list of latex nodes, function must be reset - func(Any=None, reset_lock_search=True)
    """
    def wrapped(*args, **kwargs):
        # check and add attributes
        try:
            _ = func.__flag__
            _ = func.__cache__
        except AttributeError:
            func.__flag__ = False
            func.__cache__ = ''

        # reset latch
        if 'reset_lock_search' in kwargs:
            func.__flag__ = False
            func.__cache__ = ''
            return func.__cache__

        # run main function
        if not func.__flag__:
            rez = func(*args, **kwargs)
        else:
            return func.__cache__

        # check result: bypass or lock
        if rez is None:
            return func.__cache__
        else:
            func.__flag__ = True
            func.__cache__ = rez
            return func.__cache__
    return wrapped


def get_env(nodes, env_name: str) -> Union[None, pylxt.LatexEnvironmentNode]:
    if type(nodes) is not list:
        nodes = [nodes]

    for nd in nodes:
        if type(nd) is pylxt.LatexEnvironmentNode:
            nd: pylxt.LatexEnvironmentNode

            if nd.environmentname == env_name:
                return nd
    return None


def get_document(nodes: list) -> Union[None, pylxt.LatexEnvironmentNode]:
    return get_env(nodes, 'document')


@lock_search
def get_title(node, reset_lock_search=False) -> Union[None, str]:
    if type(node) is pylxt.LatexMacroNode:
        node: pylxt.LatexMacroNode

        if node.macroname == 'title':
            return node.nodeargd.argnlist[0].nodelist[0].chars
    else:
        return None


@lock_search
def get_authors(node, reset_lock_search=False) -> Union[None, str]:
    if type(node) is pylxt.LatexMacroNode:
        node: pylxt.LatexMacroNode

        author_line = ''
        if node.macroname == 'author':
            for nd in node.nodeargd.argnlist[0].nodelist:
                if type(nd) is pylxt.LatexCharsNode:
                    nd: pylxt.LatexCharsNode

                    author_line += nd.chars

        if author_line:
            author_line = re.sub(r'\s+', ' ', author_line)

            return author_line
        else:
            return None
    else:
        return None


@lock_search
def get_abstract(node, reset_lock_search=False) -> Union[None, str]:
    env = get_env(node, 'abstract')

    if env is None:
        return None

    txt = ''
    for nd in env.nodelist:
        if type(nd) is pylxt.LatexCharsNode:
            nd: pylxt.LatexCharsNode

            txt += nd.chars
        else:
            print(nd)

    return txt


def simple_parser(latex_nodes: list) -> DataObj.Paper:
    env = get_document(paper_nodes)

    paper_obj = DataObj.Paper()

    for nd in env.nodelist:
        paper_obj.title = get_title(nd)
        paper_obj.authors = get_authors(nd)
        abst = get_abstract(nd)

    print(abst)

    get_title(None, reset_lock_search=True)
    get_authors(None, reset_lock_search=True)

    return paper_obj


if __name__ == '__main__':
    path2latex = 'arx.tex'
    with open(path2latex, 'r') as f:
        latex_txt = f.read()

    walker = pylxt.LatexWalker(latex_txt)
    paper_nodes, _, _ = walker.get_latex_nodes()

    paper = simple_parser(paper_nodes)

    print(paper.title)
    print(paper.authors)
