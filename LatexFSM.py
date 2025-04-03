from transitions import Machine

import pylatexenc.latexwalker as pylxt
from pylatexenc.latex2text import LatexNodes2Text

import re
from typing import Union

import src.DAO.DataObj as DataObj


class LatexFlowParse:
    def __init__(self, path):
        self.path = path
        self.tex = ''

        self.all_nodes = []
        self.env = []
        self.paper = DataObj.Paper()

        self.states = [
            'idle',
            'open_tex',
            'insert_cmd',
            'get_env_document',
            'get_title',
            'get_authors',
            'get_abstraction',
            'get_conclusion',
            'get_bib',
        ]

        self.last_state = 'get_env_document'

        # {
        #     'trigger': 'start_reading',
        #     'source': 'idle',
        #     'dest': 'insert_cmd',
        #     'conditions': 'pass',
        #     'before': 'pass',
        #     'after': 'pass'
        # },

        self.transitions = [
            {
                'trigger': 'run',
                'source': 'idle',
                'dest': 'open_tex',
                'after': 'load_tex',
             },
            {
                'trigger': 'run',
                'source': 'open_tex',
                'dest': 'get_env_document'
            }
        ]

        self.machine = Machine(model=self, states=self.states, transitions=self.transitions, initial=self.states[0])

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
    fsm.parse()
