from transitions import Machine

import pylatexenc.latexwalker as pylxt
from pylatexenc.latex2text import LatexNodes2Text

import re
from typing import Union, Optional

import src.DAO.DataObj as DataObj


# class LatexFlowParse:
#     def __init__(self, path):
#         self.path = path
#         self.tex = ''
#
#         self.all_nodes = []
#         self.env = []
#         self.paper = DataObj.Paper()
#
#         self.idle: Optional[str] = None
#         self.open_tex: Optional[str] = None
#         self.insert_cmd: Optional[str] = None
#         self.get_env_document: Optional[str] = None
#         self.get_title: Optional[str] = None
#         self.get_authors: Optional[str] = None
#         self.get_abstraction: Optional[str] = None
#         self.get_conclusion: Optional[str] = None
#         self.get_bib: Optional[str] = None
#         self.idle: Optional[str] = None
#
#         self.states = [
#             'idle',
#             'open_tex',
#             'insert_cmd',
#             'get_env_document',
#             'get_title',
#             'get_authors',
#             'get_abstraction',
#             'get_conclusion',
#             'get_bib',
#         ]
#
#         self.last_state = 'get_env_document'
#
#         # {
#         #     'trigger': 'start_reading',
#         #     'source': 'idle',
#         #     'dest': 'insert_cmd',
#         #     'conditions': 'pass',
#         #     'before': 'pass',
#         #     'after': 'pass'
#         # },
#
#         self.trigger: Optional[callable] = None
#
#         self.transitions = [
#             {
#                 'trigger': 'run',
#                 'source': 'idle',
#                 'dest': 'open_tex',
#                 'after': 'load_tex',
#              },
#             {
#                 'trigger': 'run',
#                 'source': 'open_tex',
#                 'dest': 'get_env_document'
#             }
#         ]
#
#         self.machine = Machine(model=self, states=self.states, transitions=self.transitions, initial=self.states[0])
#
#     def parse(self):
#         print(type(self.trigger))
#         while self.state != self.last_state:
#             self.trigger('run')
#
#     def load_tex(self):
#         try:
#             with open(self.path, 'r') as f:
#                 self.tex = f.read()
#         except Exception as e:
#             print(f"Ошибка при чтении файла: {e}")
#             return
#
#         walker = pylxt.LatexWalker(self.tex)
#         self.all_nodes, _, _ = walker.get_latex_nodes()
#
#     def get_document(self):
#         self.env = self.get_env(self.all_nodes, 'document')
#
#     @staticmethod
#     def get_env(nodes, env_name: str) -> Union[None, pylxt.LatexEnvironmentNode]:
#         if type(nodes) is not list:
#             nodes = [nodes]
#
#         for nd in nodes:
#             if type(nd) is pylxt.LatexEnvironmentNode:
#                 nd: pylxt.LatexEnvironmentNode
#
#                 if nd.environmentname == env_name:
#                     return nd
#         return None


from statemachine import StateMachine, State


class LatexFlowParse(StateMachine):
    idle = State(initial=True)
    open_tex = State()
    insert_cmd = State()

    cycle = (
        idle.to(open_tex)
        | open_tex.to(insert_cmd)
        | insert_cmd.to(idle)
    )

    def __init__(self, path):
        super().__init__()

        self.path = path
        self.tex = ''

        self.all_nodes = []
        self.env = []
        self.paper = DataObj.Paper()

    def parse(self):
        while self.state != self.last_state:
            self.trigger('run')

    def load_tex(self):
        try:
            with open(self.path, 'r') as f:
                self.tex = f.read()
        except Exception as e:
            print(f"Ошибка при чтении файла: {e}")
            return

        walker = pylxt.LatexWalker(self.tex)
        self.all_nodes, _, _ = walker.get_latex_nodes()

    def get_document(self):
        self.env = self.get_env(self.all_nodes, 'document')

    @staticmethod
    def get_env(nodes, env_name: str) -> Union[None, pylxt.LatexEnvironmentNode]:
        if type(nodes) is not list:
            nodes = [nodes]

        for nd in nodes:
            if type(nd) is pylxt.LatexEnvironmentNode:
                nd: pylxt.LatexEnvironmentNode

                if nd.environmentname == env_name:
                    return nd
        return None


if __name__ == '__main__':
    path2latex = 'data/arx.tex'

    fsm = LatexFlowParse(path2latex)
    print(fsm.current_state)
    fsm.cycle()
    print(fsm.current_state)
