from pydantic import BaseModel, ConfigDict

class BaseSchema(BaseModel):
    """
    Base Schema for Pydantic models.
    Enables ORM mode by default to work with SQLAlchemy models.
    """
    model_config = ConfigDict(from_attributes=True)
