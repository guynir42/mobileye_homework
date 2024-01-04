import sqlalchemy as sa

from models.base import Base


class Vehicle(Base):

    __tablename__ = "vehicles"

    id = sa.Column(
        sa.String,
        primary_key=True,
        nullable=False,
        doc="Unique identifier of the vehicle",
    )

    detections = sa.orm.relationship(
        "Detection",
        back_populates="vehicle",
        cascade="all, delete, delete-orphan",
        passive_deletes=True,
        doc="List of detections of the vehicle",
    )

    reports = sa.orm.relationship(
        "Report",
        back_populates="vehicle",
        cascade="all, delete, delete-orphan",
        passive_deletes=True,
        doc="List of reports of the vehicle",
    )

    # TODO: will very likely want to add stuff about the vehicle, maybe a relationship to a "driver" table, etc
