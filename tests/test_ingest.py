import os
import datetime
import json

import sqlalchemy as sa

from tests.conftest import DATA_DIR

from models.base import SmartSession
from models.reports import Report
from models.detections import Detection
from models.vehicles import Vehicle

from api.ingest import ingest


def test_ingest_detections():
    with open(os.path.join(DATA_DIR, "objects.json")) as f:
        data_string = f.read()

    with SmartSession() as session:
        det_count_start = len(session.scalars(sa.select(Detection)).all())

    status = ingest(data_string)

    assert status["status"] == "success"
    assert status["reports saved"] == 0
    assert status["detections saved"] == 7
    assert status["errors"] == []

    vid = "ebab5f787798416fb2b8afc1340d7a4e"
    times = [
        datetime.datetime.strptime("2022-06-05T21:02:34.546Z", "%Y-%m-%dT%H:%M:%S.%fZ", pytz.UTC),
        datetime.datetime.strptime("2022-06-05T21:05:20.590Z", "%Y-%m-%dT%H:%M:%S.%fZ", pytz.UTC),
        datetime.datetime.strptime("2022-06-05T21:11:35.567Z", "%Y-%m-%dT%H:%M:%S.%fZ", pytz.UTC),
    ]
    objects = [["pedestrians", "cars", "signs"], ["cars"], ["trucks", "obstacles"]]

    with SmartSession() as session:
        det_count_new = len(session.scalars(sa.select(Detection)).all())
        assert det_count_new - det_count_start == 7

        vehicle = session.scalars(sa.select(Vehicle).where(Vehicle.id == vid)).first()
        assert len(vehicle.detections) >= 7  # there is no deduplication on detections, so past test may have added some

        for time, objs in zip(times, objects):
            det = session.scalars(sa.select(Detection).where(Detection.timestamp == time)).all()
            for obj in objs:
                assert any([d.type == obj for d in det])  # this also verifies we have enough detections
            assert all([d.vehicle == vehicle for d in det])  # make sure all detections are for the right vehicle


def test_illegal_object_type():
    data = dict(
        objects_detection_events=[
            dict(
                vehicle_id="foo bar",
                detection_time="2020-01-01T00:00:00Z",
                detections=[dict(object_type="wrong!", object_value=1)],
            )
        ]
    )
    data_string = json.dumps(data)
    status = ingest(data_string)

    with SmartSession() as session:
        vehicles = session.scalars(sa.select(Vehicle).where(Vehicle.id == "foo bar")).all()
        assert len(vehicles) == 0

    assert status["status"] == "failure"
    assert any(["Invalid object type: wrong!" in err for err in status["errors"]])

    data = dict(objects_detection_key=data["objects_detection_events"])  # copy of the data but with wrong top-level key

    # not the correct top-level key, should just skip over both reports and detections
    data_string = json.dumps(data)
    status = ingest(data_string)

    assert status["status"] == "success"
    assert status["reports saved"] == 0
    assert status["detections saved"] == 0
    assert status["errors"] == []


def test_ingest_reports():
    with open(os.path.join(DATA_DIR, "statuses.json")) as f:
        data_string = f.read()

    status = ingest(data_string)

    assert status["status"] == "success"
    assert status["reports saved"] == 3
    assert status["detections saved"] == 0
    assert status["errors"] == []

    vids = [
        "ebab5f787798416fb2b8afc1340d7a4e",
        "ebae3f787798416fb2b8afc1340d7a6d",
        "qbae3f787798416fb2b8afc1340ddf19",
    ]
    times = [
        datetime.datetime.strptime("2022-05-05T22:02:34.546Z", "%Y-%m-%dT%H:%M:%S.%fZ"),
        datetime.datetime.strptime("2022-05-06T00:02:34.546Z", "%Y-%m-%dT%H:%M:%S.%fZ"),
        datetime.datetime.strptime("2022-05-09T00:02:34.546Z", "%Y-%m-%dT%H:%M:%S.%fZ"),
    ]
    statuses = ["driving", "accident", "parking"]

    # now check that the info is indeed on the DB:
    with SmartSession() as session:
        for vid, time, status in zip(vids, times, statuses):

            vehicles = session.scalars(sa.select(Vehicle).where(Vehicle.id == vid)).all()
            assert len(vehicles) == 1  # deduplication should make sure no vehicles are duplicated in the DB
            assert vehicles[0].id == vid
            assert len(vehicles[0].reports) > 0  # no deduplication on reports, so there could be more than one
            assert all([rep.status == status for rep in vehicles[0].reports])  # make sure all reports are as expected

            reports = session.scalars(sa.select(Report).where(Report.vehicle_id == vid)).all()
            assert len(reports) >= 1  # no deduplication on reports, so there could be more than one
            assert reports[0].vehicle_id == vid
            assert reports[0].timestamp == time
            assert all([rep.status == status for rep in reports])  # make sure all reports are as expected


def test_illegal_report_type():
    data = dict(
        vehicle_status=[
            dict(
                vehicle_id="foo bar",
                report_time="2020-01-01T00:00:00Z",
                status="wrong!",
            )
        ]
    )

    data_string = json.dumps(data)
    status = ingest(data_string)

    assert status["status"] == "failure"
    assert status["reports saved"] == 0
    assert status["detections saved"] == 0
    assert any(["Invalid status value: wrong!" in err for err in status["errors"]])

    with SmartSession() as session:
        vehicles = session.scalars(sa.select(Vehicle).where(Vehicle.id == "foo bar")).all()
        assert len(vehicles) == 0

    data = dict(vehicle_wrong_key=data["vehicle_status"])  # copy of the data but with wrong top-level key

    # not the correct top-level key, should just skip over both reports and detections
    data_string = json.dumps(data)
    status = ingest(data_string)

    assert status["status"] == "success"
    assert status["reports saved"] == 0
    assert status["detections saved"] == 0
    assert status["errors"] == []
