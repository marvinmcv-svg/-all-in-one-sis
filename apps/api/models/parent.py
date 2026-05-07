from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class Parent(Base, TimestampMixin):
    """Parent/guardian record linked to a person."""
    __tablename__ = "parents"

    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey("persons.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    relationship_type = Column(String(50), nullable=True)  # father, mother, guardian, etc.
    occupation = Column(String(200), nullable=True)
    income = Column(Integer, nullable=True)
    education_level = Column(String(100), nullable=True)

    # Relationships
    person = relationship("Person", back_populates="parent")
    children = relationship("Student", foreign_keys="Student.guardian_id", back_populates="guardian")

    def __repr__(self) -> str:
        return f"<Parent(id={self.id}, person_id={self.person_id}, relationship_type='{self.relationship_type}')>"
