import sqlalchemy as sa

from models.base import Base


class Report(Base):

    __tablename__ = "reports"

    id = sa.Column(
        sa.BigInteger,
        primary_key=True,
        index=True,
        autoincrement=True,
        doc="Auto-incrementing unique identifier for this report",
    )

    vehicle_id = sa.Column(
        sa.String,
        sa.ForeignKey("vehicles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="ID of the vehicle this report is associated with",
    )

    vehicle = sa.orm.relationship(
        "Vehicle",
        back_populates="detections",
        doc="Vehicle this report is associated with",
    )

    status = sa.Column(
        sa.String,  # TODO: consider using an enum or an int that is translated to one of a set of strings
        nullable=False,
        index=True,
        doc="Status of the vehicle. Possible values are: parking, driving, accident. ",
    )

    timestamp = sa.Column(
        sa.DateTime,
        nullable=False,
        index=True,
        doc="Timestamp of the report. ",
    )


def __setattr__(self, key, value):
    """
    Check inputs to this object.
    """
    # TODO: this is nice but it is better to enforce enum-type strings at the DB level
    if key == "status" and value not in ["parking", "driving", "accident"]:
        raise ValueError(f"Invalid status value: {value}")

    super().__setattr__(key, value)
