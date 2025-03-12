from pydantic import BaseModel
from typing import List, Union, Dict
from dataclasses import field
import logging

import json


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('../../processing.log'), logging.StreamHandler()]
)


class PaperDocPiece(BaseModel):
    string: str = ''


class PaperDocEquation(BaseModel):
    latex: str = ''


class PaperDocPicture(BaseModel):
    link: str = ''
    type_img: str = ''

    title: str = ''


class PaperDocTable(BaseModel):
    markdown: str = ''


class PaperDocReference(BaseModel):
    number: int = None
    title: str = ''
    authors: str = ''

    link: str = ''


class PaperDoc(BaseModel):
    text: List[PaperDocPiece] = field(default_factory=lambda: [PaperDocPiece()])
    equations: List[PaperDocEquation] = field(default_factory=lambda: [PaperDocEquation()])
    pictures: List[PaperDocPicture] = field(default_factory=lambda: [PaperDocPicture()])
    tables: List[PaperDocTable] = field(default_factory=lambda: [PaperDocTable()])
    bibliography: List[PaperDocReference] = field(default_factory=lambda: [PaperDocReference()])

    graph: List[dict[str, int]] = None


class Paper(BaseModel):
    title: str = ''
    title_id: str = ''
    summary: str = ''

    link_paper: str = ''
    version: int = 0

    doc: PaperDoc = PaperDoc()

    vec: List[Union[int, float]] = None
    index: int = 0


def load_paper(paper: Paper, path: str) -> Paper:
    try:
        with open(path, 'r') as f:
            content_saved = f.read()
        paper_upd = paper.model_validate_json(content_saved)
    except FileNotFoundError:
        logging.warning("File not found: " + path)
        paper_upd = paper

    return paper_upd


def save_paper(paper: Paper, filename: str) -> None:
    with open(filename, "w") as f:
        f.write(paper.model_dump_json(indent=4, exclude_none=True))


if __name__ == "__main__":
    path2json = "obj_json_text.json"

    paper = Paper()

    paper = load_paper(paper, path2json)
    print(paper.model_dump_json(indent=4))

    paper.title = "Auf"
    paper.link_paper = "https://les/staya/auf_volki.html"
    paper.summary = "Aauuuuuuuuuuf"

    print(paper.model_dump_json(indent=4))

    save_paper(paper, path2json)
