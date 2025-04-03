import pylatexenc.latexwalker as pylxt
from pylatexenc.latex2text import LatexNodes2Text
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
    env = get_env(nodes, 'document')
    return env


def flatten_env(nested_list: list) -> list:
    result = []
    for i in nested_list:
        try:
            if isinstance(i.nodelist, list):
                result += flatten_env(i.nodelist)
        except AttributeError:
            result.append(i)
    return result


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

        if node.macroname == 'author':
            latex_to_text = LatexNodes2Text()
            txt = latex_to_text.nodelist_to_text([node.nodeargd.argnlist[0]])
            txt = re.sub(r'\s+', ' ', txt)

            return txt
    else:
        return None


@lock_search
def get_abstract(node, reset_lock_search=False) -> Union[None, str]:
    env = get_env(node, 'abstract')

    if env is None:
        return None

    latex_to_text = LatexNodes2Text()
    txt = latex_to_text.nodelist_to_text([env])
    txt = re.sub(r'\s+', ' ', txt)

    return txt


def simple_parser(latex_nodes: list) -> DataObj.Paper:
    env = get_document(paper_nodes)

    # print(env.nodelist)

    env_flatten = flatten_env(env.nodelist)

    with open('temp/output.txt', 'w') as f:
        for i in env_flatten:
            # if type(i) is pylxt.LatexMacroNode:
            #     # print(i)
            #     if i.macroname == "%":
            #         f.write("%")
            #
            #     continue
            # else:
            #     pass

            try:
                # f.write(i.chars)

                f.write(str(i) + "\n\n\n")
            except AttributeError:
                pass

    paper_obj = DataObj.Paper()

    for nd in env.nodelist:
        paper_obj.title = get_title(nd)
        paper_obj.authors = get_authors(nd)
        paper_obj.doc.abstract = get_abstract(nd)

    get_title(None, reset_lock_search=True)
    get_authors(None, reset_lock_search=True)
    get_abstract(None, reset_lock_search=True)

    return paper_obj


if __name__ == '__main__':
    path2latex = 'data/arx.tex'
    with open(path2latex, 'r') as f:
        latex_txt = f.read()

    walker = pylxt.LatexWalker(latex_txt)
    paper_nodes, _, _ = walker.get_latex_nodes()

    paper = simple_parser(paper_nodes)

    print(paper.title)
    print(paper.authors)
    print(paper.doc.abstract)
