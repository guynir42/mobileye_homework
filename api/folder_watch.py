import os
import time

from api.ingest import ingest


def watcher(
    working_dir=None, interval=1, timeout=None, delay=None, session=None, statuses=None
):
    """
    Watches a directory for new files and ingests them.

    Parameters
    ----------
    working_dir: str
        Directory to watch. Defaults to current working directory.
    interval: float
        Time in seconds between checks for new files.
    timeout: float, optional
        Time in seconds to watch the directory. If None, watch forever.
    delay: delay, optional
        Time in seconds to wait before starting to watch the directory.
    session: sqlalchemy.orm.Session, optional
        Database session to use. If None, will create a new session each time ingest is called.

    Returns
    -------
    statuses: list
        A list of dictionaries with the status of each ingest call.
    """
    if working_dir is None:
        working_dir = os.getcwd()

    start_time = time.time()

    if statuses is None:  # if not None, will append to input as an output
        statuses = []

    while True:
        if timeout is not None and time.time() - start_time > timeout:
            break
        if delay is not None and time.time() - start_time < delay:
            continue

        json_files = [
            os.path.join(working_dir, f)
            for f in os.listdir(working_dir)
            if f.endswith(".json")
        ]
        # print(f'files in {working_dir}: {json_files}')

        for f in json_files:
            with open(f) as fid:
                json_string = fid.read()
            status = ingest(json_string, session=session)
            statuses.append(status)
            os.remove(
                f
            )  # TODO: add option to send file to archive instead of deleting it

        time.sleep(interval)

    return statuses
