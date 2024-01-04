import sqlalchemy as sa

from models.base import Base


class Detection(Base):
    id = sa.Column(
        sa.BigInteger,
        primary_key=True,
        index=True,
        autoincrement=True,
        doc="Auto-incrementing unique identifier for this detection",
    )

    vehicle_id = sa.Column(
        sa.String,
        sa.ForeignKey("vehicles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="ID of the vehicle this detection is associated with",
    )

    vehicle = sa.orm.relationship(
        "Vehicle",
        back_populates="detections",
        doc="Vehicle this detection is associated with",
    )

    type = sa.Column(
        sa.String,  # TODO: consider using an enum or an int that is translated to one of a set of strings
        nullable=False,
        index=True,
        doc="Type of object detected. Possible values are: pedestrians, cars, signs. ",
    )

    value = sa.Column(
        sa.Float,  # TODO: I am not sure if this information is just a placeholder, so maybe an int is ok too?
        nullable=False,
        index=True,
        doc="Value of the detection. For example, the speed of a car, or the number of pedestrians. ",
    )

    timestamp = sa.Column(
        sa.DateTime,
        nullable=False,
        index=True,
        doc="Timestamp of the detection. ",
    )


def __setattr__(self, key, value):
    """
    Check inputs to this object.
    """
    # TODO: this is nice but it is better to enforce enum-type strings at the DB level
    if key == "type" and value not in ["pedestrians", "cars", "signs"]:
        raise ValueError(f"Invalid object type: {value}")

    super().__setattr__(key, value)
