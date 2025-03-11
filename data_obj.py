from pydantic import BaseModel
from typing import List, Union
import logging

import json


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('processing.log'), logging.StreamHandler()]
)


def load_paper(path):
    try:
        with open(path2json, 'r') as f:
            content_saved = json.load(f)
        obj = Paper(**content_saved)
    except FileNotFoundError:
        logging.warning("File not found: " + path)
        obj = None

    return obj


class PaperDocPiece(BaseModel):
    pass


class PaperDocEquation(BaseModel):
    pass


class PaperDocPicture(BaseModel):
    pass


class PaperDocTable(BaseModel):
    pass


class PaperDocReference(BaseModel):
    pass


class PaperDoc(BaseModel):
    text: List[PaperDocPiece]
    equations: List[PaperDocEquation]
    pictures: List[PaperDocPicture]
    tables: List[PaperDocTable]
    bibliography: List[PaperDocReference]

    graph: List[dict[str, int]]


class Paper(BaseModel):
    title: str
    title_id: str
    summary: str

    link_paper: str
    version: int

    doc: PaperDoc

    vec: List[Union[int, float]]
    index: int


if __name__ == "__main__":
    path2json = "obj_json_text.json"

    content = {
        "title": "Flattened Convolutional Neural Networks For Feedforward Acceleration",
        "title_id": "2110.00476",
        "summary": "We present flattened convolutional neural networks that are designed for fast feedforward execution. The redundancy of the parameters, especially weights of the convolutional filters in convolutional neural networks has been extensively studied and different heuristics have been proposed to construct a low rank basis of the filters after training. In this work, we train flattened networks that consist of consecutive sequence of one-dimensional filters across all directions in 3D space to obtain comparable performance as conventional convolutional networks. We tested flattened model on different datasets and found that the flattened layer can effectively substitute for the 3D filters without loss of accuracy. The flattened convolution pipelines provide around two times speed-up during feedforward pass compared to the baseline model due to the significant reduction of learning parameters. Furthermore, the proposed method does not require efforts in manual tuning or post processing once the model is trained.",
        "link_paper": "https://arxiv.org/abs/1412.5474",
        "link_github": "",
        "version": 4,
        "doc": {},
        "vec": [],
        "index": 0
    }

    obj = load_paper(path2json)

    if obj is None:
        obj = Paper(**content)

    print(obj.title)
    obj_json = obj.model_dump_json()
    print(obj_json)

    with open(path2json, 'w') as f:
        f.write(obj_json)
