# Mobileye_homework

Home assignment for a job interview at mobileye

### Models

We have three models in the database, based on the input file structure:

- `Vehicle`: has a unique ID and relationships to the other models.
- `Report`: a status of the vehicle, can have status equal "driving", "parking", or "accident". Also has timestamp.
- `Detection`: a detection of an object, has a type ("car", "truck", "pedestrians", "signs" or "obstacles"),
  and a value (e.g., could represent the distance to the object). Also has a timestamp for when the detection was made.

### API

To ingest a string of data, formatted as JSON, use `api.ingest.ingest()`.
This function will accept a string, parse the top-level dictionary item,
decide if it contains detections or reports, and then calls the low-level
function `ingest_detections` or `ingest_reports` accordingly.

The function returns a dictionary with the following keys:

- `status`: "success" or "failure"
- `errors`: a list of errors, if any
- `reports saved`: number of reports saved
- `detections saved`: number of detections saved

The function deliberately does not raise exceptions, so it can be used in a loop.
Please make sure to check the `status` key in the returned dictionary.

### Looping on input files

To check if a folder has received any new files, use `api.folder_watch.watcher()`.
This function gets a string path to a folder, and some parameters for the length of the loop
and the interval, etc.
If any files ending with `.json` are found in the folder, they are ingested using the `ingest` function.
The function returns a list of dictionaries, each containing the results of the ingestion of a single file.

### Alternaive ingestion methods

In the future, it would make sense to use an http server to ingest the data,
which could still use the `ingest` method, only it would be called whenever a user
sends a POST request to the server.

### Queries

Although it is possible to run sqlalchemy queries directly, or even use raw SQL against the DB,
we provide a module with some useful shortcuts.
This is found in `api.query`.
There are three functions:

- `get_vehicle()`: returns a vehicle object, given its ID.
- `get_reports()`: returns a list of reports, given some parameters like vehicle ID or start/end time.
- `get_detections()`: returns a list of detections, given some parameters like vehicle ID or start/end time.

For more information, see the docstring of each function.

### Database Sessions

To connect to the database we use postgresql, with sqlalchemy as a mapper from database rows to python objects.
Accessing the DB is done using a session object.
Each function in the stack accepts an optional `session` keyword.
If given, the function will use that external session.
If not given, a new session will be opened in the function scope,
and closed internally before the function terminates.
This makes sure we do not leave open sessions, that could take up valuable resources.

Since nested functions would inherit the session from the parent function,
the user can choose at what level the session should be opened/closed,
and it will be passed down to the lower-level functions.

### Tests

Tests are found in the `tests` folder, and use the example files in `data` to check the functionality of the code.
