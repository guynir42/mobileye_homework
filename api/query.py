import sqlalchemy as sa

from models.base import SmartSession
from models.reports import Report
from models.detections import Detection
from models.vehicles import Vehicle


def get_vehicle(vehicle_id, session=None):
    """
    Get a vehicle by its ID.
    """
    with SmartSession(session) as session:
        vehicle = session.scalars(sa.select(Vehicle).where(Vehicle.id == vehicle_id)).first()
        return vehicle


def get_reports(statuses=None, start_time=None, end_time=None, vehicle_id=None, session=None):
    """
    Get reports matching the given criteria.

    Parameters
    ----------
    statuses : str or list of str, optional
        Statuses to match. If None, all statuses are matched.
    start_time : datetime.datetime, optional
        Match reports that were made after this time. If None, do not filter by start time.
    end_time : datetime.datetime, optional
        Match reports that were made before this time. If None, do not filter by end time.
    """
    if isinstance(statuses, str):
        statuses = [statuses]

    with SmartSession(session) as session:
        stmt = sa.select(Report)
        if statuses is not None:
            stmt = stmt.where(Report.status.in_(statuses))
        if start_time is not None:
            stmt = stmt.where(Report.timestamp >= start_time)
        if end_time is not None:
            stmt = stmt.where(Report.timestamp <= end_time)
        if vehicle_id is not None:
            stmt = stmt.where(Report.vehicle_id == vehicle_id)
        reports = session.scalars(stmt).all()

        return reports


def get_detections(
    types=None,
    exact_values=None,
    value_minimum=None,
    value_maximum=None,
    start_time=None,
    end_time=None,
    vehicle_id=None,
    session=None,
):
    """
    Get detections matching the given criteria.

    Parameters
    ----------
    types : str or list of str, optional
        Object types to match. If None, all object types are matched.
    exact_values : str or list of str, optional
        Object values to match. If None, all object values are matched.
    value_minimum : float, optional
        Match detections with values greater than or equal to this value. If None, do not filter by minimum value.
    value_maximum : float, optional
        Match detections with values less than or equal to this value. If None, do not filter by maximum value.
    start_time : datetime.datetime, optional
        Match detections that were made after this time. If None, do not filter by start time.
    end_time : datetime.datetime, optional
        Match detections that were made before this time. If None, do not filter by end time.
    """
    if isinstance(types, str):
        types = [types]
    if isinstance(exact_values, float):
        exact_values = [exact_values]

    with SmartSession(session) as session:
        stmt = sa.select(Detection)
        if types is not None:
            stmt = stmt.where(Detection.type.in_(types))
        if exact_values is not None:
            stmt = stmt.where(Detection.value.in_(exact_values))
        if value_minimum is not None:
            stmt = stmt.where(Detection.value >= value_minimum)
        if value_maximum is not None:
            stmt = stmt.where(Detection.value <= value_maximum)
        if start_time is not None:
            stmt = stmt.where(Detection.timestamp >= start_time)
        if end_time is not None:
            stmt = stmt.where(Detection.timestamp <= end_time)
        if vehicle_id is not None:
            stmt = stmt.where(Detection.vehicle_id == vehicle_id)

        detections = session.scalars(stmt).all()

        return detections
