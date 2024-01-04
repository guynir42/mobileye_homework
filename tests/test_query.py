import os
import datetime
import json

import sqlalchemy as sa

from tests.conftest import DATA_DIR

from models.base import SmartSession
from models.reports import Report
from models.detections import Detection
from models.vehicles import Vehicle

from api.query import get_reports, get_detections, get_vehicle
from api.ingest import ingest


def test_query_parameters():
    vehicle_ids = [
        "ebab5f787798416fb2b8afc1340d7a4e",
        "ebae3f787798416fb2b8afc1340d7a6d",
        "qbae3f787798416fb2b8afc1340ddf19",
        "foo bar",
    ]

    # clear the database
    with SmartSession() as session:
        vehicles = session.scalars(sa.select(Vehicle).where(Vehicle.id.in_(vehicle_ids))).all()
        assert len(vehicles) <= 4  # vehicle ids are unique!
        [session.delete(v) for v in vehicles]
        session.commit()

    with open(os.path.join(DATA_DIR, "objects.json")) as f:
        data_string = f.read()
    status = ingest(data_string)
    print(status)
    assert status["status"] == "success"

    with open(os.path.join(DATA_DIR, "statuses.json")) as f:
        data_string = f.read()
    status = ingest(data_string)
    assert status["status"] == "success"

    # check we can get the vehicle:
    with SmartSession() as session:  # load in a session so we can lazy load relationships
        vid = vehicle_ids[0]
        vehicle = get_vehicle(vid, session=session)
        assert vehicle.id == vid
        assert len(vehicle.detections) == 7
        assert len(vehicle.reports) == 1
        assert vehicle.reports[0].status == "driving"

        vid = vehicle_ids[1]
        vehicle = get_vehicle(vid, session=session)
        assert vehicle.id == vid
        assert len(vehicle.detections) == 0
        assert len(vehicle.reports) == 1
        assert vehicle.reports[0].status == "accident"

        # check that we can query using different filters
        # query for reports
        # filter by statuses
        reports = get_reports(statuses="driving", session=session)
        assert len(reports) == 1
        assert reports[0].status == "driving"
        assert reports[0].vehicle_id == vehicle_ids[0]

        reports = get_reports(statuses="accident", session=session)
        assert len(reports) == 1
        assert reports[0].status == "accident"
        assert reports[0].vehicle_id == vehicle_ids[1]
        assert reports[0].vehicle == vehicle  # that last vehicle is the same as we got above

        reports = get_reports(statuses=["driving", "accident"], session=session)
        assert len(reports) == 2

        # filter by start and end times
        reports = get_reports(start_time=datetime.datetime(2022, 5, 5, 0, 0, 0, 0), session=session)
        assert len(reports) == 3

        reports = get_reports(start_time=datetime.datetime(2022, 5, 6, 0, 0, 0, 0), session=session)
        assert len(reports) == 2

        reports = get_reports(start_time=datetime.datetime(2022, 5, 9, 0, 0, 0, 0), session=session)
        assert len(reports) == 1

        reports = get_reports(end_time=datetime.datetime(2022, 5, 5, 0, 0, 0, 0), session=session)
        assert len(reports) == 0

        reports = get_reports(end_time=datetime.datetime(2022, 5, 6, 0, 0, 0, 0), session=session)
        assert len(reports) == 1

        reports = get_reports(end_time=datetime.datetime(2022, 5, 9, 0, 0, 0, 0), session=session)
        assert len(reports) == 2

        reports = get_reports(start_time=datetime.datetime(2022, 5, 5, 0, 0, 0, 0), session=session)
        assert len(reports) == 3

        reports = get_reports(start_time=datetime.datetime(2022, 5, 6, 0, 0, 0, 0), session=session)
        assert len(reports) == 2

        reports = get_reports(
            start_time=datetime.datetime(2022, 5, 6, 0, 0, 0, 0),
            end_time=datetime.datetime(2022, 5, 9, 0, 0, 0),
            session=session,
        )
        assert len(reports) == 1
        assert reports[0].status == "accident"
        assert reports[0].vehicle_id == vehicle_ids[1]

        # query for detections
        # filter by types
        detections = get_detections(types="cars", session=session)
        assert len(detections) == 2
        assert all([det.type == "cars" for det in detections])
        assert all([det.vehicle_id == vehicle_ids[0] for det in detections])

        detections = get_detections(types="trucks", session=session)
        assert len(detections) == 1
        assert detections[0].type == "trucks"
        assert detections[0].vehicle_id == vehicle_ids[0]
        assert detections[0].value == 5.0

        detections = get_detections(types=["cars", "trucks"], session=session)
        assert len(detections) == 3

        # filter by exact values
        detections = get_detections(exact_values=5.0, session=session)
        assert len(detections) == 1
        assert detections[0].type == "trucks"

        detections = get_detections(exact_values=[5.0, 1.0], session=session)
        assert len(detections) == 1
        assert detections[0].type == "trucks"

        # filter by value range
        detections = get_detections(value_minimum=4.0, session=session)
        assert len(detections) == 2
        assert all([det.value >= 4.0 for det in detections])
        assert {"trucks", "cars"} == {det.type for det in detections}

        detections = get_detections(value_maximum=4.0, session=session)
        assert len(detections) == 6
        assert all([det.value <= 4.0 for det in detections])
        assert {"pedestrians", "signs", "obstacles", "cars"} == {det.type for det in detections}  # no trucks!

        detections = get_detections(value_minimum=4.5, value_maximum=5.5, session=session)
        assert len(detections) == 1
        assert detections[0].type == "trucks"
        assert detections[0].value == 5.0

        # try the start and end times
        detections = get_detections(start_time=datetime.datetime(2022, 6, 5, 21, 5, 20, 0), session=session)
        assert len(detections) == 3
        assert {"obstacles", "trucks", "cars"} == {det.type for det in detections}

        detections = get_detections(end_time=datetime.datetime(2022, 6, 5, 21, 5, 20, 0), session=session)
        assert len(detections) == 4
        assert {"pedestrians", "signs", "cars"} == {det.type for det in detections}

        # check that mixed filters work
        detections = get_detections(
            end_time=datetime.datetime(2022, 6, 5, 21, 5, 20, 0), types="pedestrians", session=session
        )
        assert len(detections) == 2
        assert all([det.type == "pedestrians" for det in detections])
