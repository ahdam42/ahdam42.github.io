import pytest
from src.utils.utils import normalize_arxiv_id

@pytest.mark.parametrize(
    "input_id, expected",
    [
        ("arXiv:1501.00001", "arxiv:1501.00001"),
        (" arXiv:1501.00001  ", "arxiv:1501.00001"),
    ]
)

def test_normalize_arxiv_id(input_id: str, expected: str):
    assert normalize_arxiv_id(input_id) == expected
