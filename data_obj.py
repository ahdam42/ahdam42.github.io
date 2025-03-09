from pydantic import BaseModel


class Delivery(BaseModel):
    dimensions: tuple[int, int]
