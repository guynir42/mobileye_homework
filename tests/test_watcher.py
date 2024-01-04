import os
import time
import shutil

import sqlalchemy as sa

from functools import partial
from multiprocessing import Pool

from models.base import CODE_ROOT, SmartSession
from models.vehicles import Vehicle
from models.reports import Report
from models.detections import Detection

from api.folder_watch import watcher


def test_watcher_new_files():
    temp_dir = os.path.join(CODE_ROOT, "temp")
    try:
        if not os.path.isdir(temp_dir):
            os.makedirs(temp_dir)

        vehicle_ids = [
            "ebab5f787798416fb2b8afc1340d7a4e",
            "ebae3f787798416fb2b8afc1340d7a6d",
            "qbae3f787798416fb2b8afc1340ddf19",
        ]

        # clear the database
        with SmartSession() as session:
            vehicles = session.scalars(
                sa.select(Vehicle).where(Vehicle.id.in_(vehicle_ids))
            ).all()
            assert len(vehicles) <= 3  # vehicle ids are unique!
            [session.delete(v) for v in vehicles]
            session.commit()

            vehicles = session.scalars(
                sa.select(Vehicle).where(Vehicle.id.in_(vehicle_ids))
            ).all()
            assert len(vehicles) == 0

            # check the detections and reports are all gone, too
            detections = session.scalars(
                sa.select(Detection).where(Detection.vehicle_id.in_(vehicle_ids))
            ).all()
            assert len(detections) == 0

            reports = session.scalars(
                sa.select(Report).where(Report.vehicle_id.in_(vehicle_ids))
            ).all()
            assert len(reports) == 0

        p = Pool(1)
        output = p.map_async(
            partial(watcher, timeout=1, interval=0.1, delay=0.2), [temp_dir]
        )
        p.close()
        p.join()
        statuses = output.get()[0]
        # check that this works without files
        assert len(statuses) == 0

        # copy the demo files into the temp directory
        p = Pool(1)
        output = p.map_async(
            partial(watcher, timeout=1, interval=0.1, delay=0.2), [temp_dir]
        )

        data_dir = os.path.join(CODE_ROOT, "data")
        for f in os.listdir(data_dir):
            if f.endswith(".json"):
                # print(f'copying {f} to {temp_dir}')
                shutil.copy2(os.path.join(data_dir, f), temp_dir)

        p.close()
        p.join()
        statuses = output.get()[0]
        assert len(statuses) == 2

        successes = [stat["status"] == "success" for stat in statuses]
        assert all(successes)

        # should find 0 and 7 detections
        dets = [stat["detections saved"] for stat in statuses]
        assert 0 in dets
        assert 7 in dets

        # should find 0 and 3 reports
        reps = [stat["reports saved"] for stat in statuses]
        assert 0 in reps
        assert 3 in reps

        # check the DB contains the correct objects:
        with SmartSession() as session:
            vehicles = session.scalars(
                sa.select(Vehicle).where(Vehicle.id.in_(vehicle_ids))
            ).all()
            assert len(vehicles) == 3

            # check the detections
            detections = session.scalars(
                sa.select(Detection).where(Detection.vehicle_id.in_(vehicle_ids))
            ).all()
            assert len(detections) == 7
            assert {"pedestrians", "cars", "signs", "trucks", "obstacles"} == {
                det.type for det in detections
            }

            reports = session.scalars(
                sa.select(Report).where(Report.vehicle_id.in_(vehicle_ids))
            ).all()
            assert len(reports) == 3
            assert {"parking", "driving", "accident"} == {rep.status for rep in reports}

            assert len(os.listdir(temp_dir)) == 0

    finally:  # cleanup

        if os.path.isdir(temp_dir):
            shutil.rmtree(temp_dir)
