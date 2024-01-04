import json
import traceback
import sqlalchemy as sa

from models.base import SmartSession
from models.reports import Report
from models.detections import Detection
from models.vehicles import Vehicle


def make_empty_status():
    return {
        "status": "success",
        "errors": [],
        "reports saved": 0,
        "detections saved": 0,
    }


def get_vehicle(vehicle_id, session=None):
    """
    Try to find the vehicle with the given ID in the database.
    If it doesn't exist, a new one will be generated.
    Note that if this function is not given a session,
    the output vehicle object may become detached and
    will need to be merged into a new session.
    If the vehicle is not found and new vehicle is returned,
    it is not automatically added to the session or saved to DB.

    Parameters
    ----------
    vehicle_id: str
        The ID of the vehicle to look, or it is created with this ID.
    session: sqlalchemy.orm.session.Session, optional
        A session to use for the database connection. If not given, a new session will be created.
        If a new session is created, it will also be closed at the end of the call.

    Returns
    -------
    vehicle: Vehicle
        The vehicle object with the given ID.
    """
    with SmartSession(session) as session:
        vehicle = session.scalars(
            sa.select(Vehicle).where(Vehicle.id == vehicle_id)
        ).first()
        if vehicle is None:
            vehicle = Vehicle(id=vehicle_id)

        return vehicle


def ingest(data, session=None):
    """
    Read the content of a string of data (JSON formatted), verify that the data is compatible,
    and save it into the database.
    Returns a dictionary with a report on success/failure and any errors.

    Parameters
    ----------
    data: str
        A JSON formatted string with the content of a file or stream of data.

    session: sqlalchemy.orm.session.Session, optional
        A session to use for the database connection. If not given, a new session will be created.
        If a new session is created, it will also be closed at the end of the call.

    Returns
    -------
    status_report: dict
        A dictionary with a report on success/failure and any errors.
        Will contain the following keys:
        - status: str
            Either 'success' or 'failure'.
        - errors: list
            A list of strings with error messages.
        - reports saved: int
            The number of reports saved into the database.
        - detections saved: int
            The number of detections saved into the database.
    """
    status_report = make_empty_status()

    try:
        try:
            data_dict = json.loads(data)
        except Exception:
            status_report["status"] = "failure"
            status_report["errors"] = f"Could not parse data: {traceback.format_exc()}"
            return  # will go to finally and return the status_report from there

        # are we allowing a file to have both detections and reports? if not, turn into an if-else
        if "vehicle_status" in data_dict.keys():  # we got a file with status reports:
            ingest_reports(data_dict["vehicle_status"], status_report, session=session)
        if "objects_detection_events" in data_dict.keys():
            ingest_detections(
                data_dict["objects_detection_events"], status_report, session=session
            )

    finally:
        return status_report  # will accumulate errors along the way


def ingest_reports(report_list, status_report=None, session=None):
    """
    Ingest a list of status reports into the database.

    Parameters
    ----------
    report_list: list
        A list of status reports. Each report is a dictionary with the following keys:
        - vehicle_id: str
            The ID of the vehicle this report is associated with.
        - status: str
            The status of the vehicle. Possible values are: 'parking', 'driving', 'accident'.
        - timestamp: str
            The timestamp of the report.
    status_report: dict, optional
        A dictionary with a report on success/failure and any errors.
        If not given, a new one is created.
    session: sqlalchemy.orm.session.Session, optional
        A session to use for the database connection. If not given, a new session will be created.
        If a new session is created, it will also be closed at the end of the call.

    Returns
    -------
    None
    """
    try:
        if status_report is None:
            status_report = make_empty_status()
        with SmartSession(session) as session:
            for report in report_list:
                try:
                    vehicle = get_vehicle(report["vehicle_id"], session=session)
                    # TODO: this would be a great place to check for duplicates!
                    db_report = Report(
                        vehicle=vehicle,
                        status=report["status"],
                        timestamp=report["report_time"],
                    )
                    session.add(db_report)
                    status_report["reports saved"] += 1
                except Exception:
                    status_report["status"] = "failure"
                    status_report["errors"].append(
                        f"Could not save report: {traceback.format_exc()}"
                    )
                    return

            session.commit()

    except Exception:
        status_report["status"] = "failure"
        status_report["errors"].append(
            f"Could not save reports: {traceback.format_exc()}"
        )


def ingest_detections(event_list, status_report=None, session=None):
    """
    Ingest a list of events, each containing a list of detections that go into the database.

    Parameters
    ----------
    event_list: list
        A list of object detection events. Each event is a dictionary with the following keys:
        - vehicle_id: str
            The ID of the vehicle this detection is associated with.
        - timestamp: str
            The timestamp of the detections.
        - detections: list
            A list of detection dictionaries, each containing:
            * object_type: str
                The type of object detected. Possible values are: 'pedestrians', 'cars', 'signs'.
            * object_value: float
                The value of the detection. For example, the speed of a car, or the number of pedestrians.
    status_report: dict, optional
        A dictionary with a report on success/failure and any errors.
        If not given, a new one is created.
    session: sqlalchemy.orm.session.Session, optional
        A session to use for the database connection. If not given, a new session will be created.
        If a new session is created, it will also be closed at the end of the call.

    Returns
    -------
    None

    """
    try:
        if status_report is None:
            status_report = make_empty_status()
        with SmartSession(session) as session:
            for event in event_list:
                try:
                    vehicle = get_vehicle(event["vehicle_id"], session=session)
                    time = event["detection_time"]
                    for detection in event["detections"]:
                        try:
                            # TODO: this would be a great place to check for duplicates!
                            db_detection = Detection(
                                vehicle=vehicle,
                                type=detection["object_type"],
                                value=detection["object_value"],
                                timestamp=time,
                            )
                            session.add(db_detection)
                            status_report["detections saved"] += 1
                        except Exception:
                            status_report["status"] = "failure"
                            status_report["errors"].append(
                                f"Could not save detection: {traceback.format_exc()}"
                            )
                            return

                except Exception:
                    status_report["status"] = "failure"
                    status_report["errors"].append(
                        f"Could not save event: {traceback.format_exc()}"
                    )
                    return

            session.commit()

    except Exception:
        status_report["status"] = "failure"
        status_report["errors"].append(
            f"Could not save reports: {traceback.format_exc()}"
        )
