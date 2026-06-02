"""FastAPI entrypoint exposing the platform's HTTP API.

Endpoints cover user auth (signup/login), CSV ingestion, and triggering the three
pipeline stages (data processing, forecasting, metrics) plus run-status lookup. The
long-running stages are dispatched as FastAPI background tasks, which in turn fan work
out to Celery workers.
"""
import os

from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from control.control_modal import generate_ingest_id, ingest_data, data_processing_pipeline, forecasting_pipeline
from control.db_modal import UserTable
from control.control_helper import get_user_id, verify_user, insert_user, verify_user_id, \
    get_dp_train_ids, \
    get_default_dp_parameters, insert_train_parameters_to_db, copy_existing_dp_data_id, get_fcst_train_ids, \
    copy_existing_fcst_data_id, get_default_fcst_parameters, verify_metrics_exists, get_train_history
from metrics.metrics_pipeline import calculate_metric


app = FastAPI()
origins = [
    "http://localhost",
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/test")
async def test():
    """Health check; returns a static payload to confirm the API is up."""
    return {"Hello": "World"}


@app.post("/signup")
async def signup(user: UserTable):
    """Register a new user, rejecting blank or already-taken usernames."""
    if user.user_password == "":
        return {"status": "FAILURE", "message": "Password is required"}, 400
    if user.user_name == "":
        return {"status": "FAILURE", "message": "Username is required"}, 400
    user_id = get_user_id(user.user_name)
    if user_id == 0:
        insert_user(user.user_name, user.user_password)
        return {"status": "SUCCESS", "message": "User Inserted"}, 200
    else:
        return {"status": "FAILURE", "message": "Username already exists"}, 400


@app.post("/login")
async def login(user: UserTable):
    """Authenticate a user and return their user_id on success."""
    if user.user_password == "":
        return {"status": "FAILURE", "message": "Password is required"}, 400
    if user.user_name == "":
        return {"status": "FAILURE", "message": "Username is required"}, 400
    verify_status = verify_user(user.user_name, user.user_password)
    if verify_status:
        user_id = get_user_id(user.user_name)
        return {"status": "SUCCESS", "user_id": user_id}, 200
    else:
        return {"status": "FAILURE", "message": "Username or password is incorrect"}, 400


@app.post("/upload-ingestion-data")
async def upload_ingestion_data(background_tasks: BackgroundTasks, user_id: int = Form(...), file: UploadFile = File(...)):
    """Save an uploaded CSV and kick off ingestion in the background.

    Returns the generated train_id/data_id immediately; the actual load runs async.
    """
    if user_id == 0:
        return {"status": "FAILURE", "message": "User Id is required"}, 400
    if file.filename == "":
        return {"status": "FAILURE", "message": "File is required"}, 400
    if verify_user_id(user_id):
        train_id, data_id = generate_ingest_id()
        os.makedirs("control/raw_data", exist_ok=True)
        file_location = f"control/raw_data/{file.filename}"
        with open(file_location, "wb+") as file_object:
            file_object.write(file.file.read())
        background_tasks.add_task(ingest_data, train_id, data_id, file.filename, user_id)
        return {"status": "SUCCESS", "train_id": train_id, "data_id": data_id}, 200
    else:
        return {"status": "FAILURE", "message": "User not verified"}, 400


@app.get('/get-default-data-processing-parameters')
async def get_dp_parameters():
    """Return the default data-processing parameters and their allowed ranges."""
    return {"status": "SUCCESS", "parameters": get_default_dp_parameters()}, 200


@app.post('/get-dp-train-ids')
async def get_dp_train(user_id: int = Form(...), train_type: str = Form(...)):
    """List train_ids eligible for data processing (new vs. re-run) for a user."""
    if verify_user_id(user_id):
        train_id = get_dp_train_ids(train_type, user_id)
        return {"status": "SUCCESS", "train_id": train_id}, 200
    else:
        return {"status": "FAILURE", "message": "User not verified"}, 400


@app.post('/trigger-data-processing')
async def trigger_dp(background_tasks: BackgroundTasks, user_id: int = Form(...), train_id: int = Form(...), parameters: str = Form(...), train_type: str = Form(...)):
    """Persist parameters and run the data-processing pipeline in the background.

    train_type 'create' uses the given train_id; 'existing' clones it to a new run.
    """
    if verify_user_id(user_id):
        if train_type == "create":
            insert_train_parameters_to_db(train_id, parameters)
            background_tasks.add_task(data_processing_pipeline, train_id)
        elif train_type == "existing":
            new_train_id = copy_existing_dp_data_id(train_id)
            insert_train_parameters_to_db(new_train_id, parameters)
            background_tasks.add_task(data_processing_pipeline, new_train_id)
        return {"status": "SUCCESS", "message": "Data processing triggered"}, 200
    else:
        return {"status": "FAILURE", "message": "User not verified"}, 400


@app.get('/get-default-forecasting-parameters')
async def get_dp_parameters():
    """Return the default forecasting parameters and their allowed ranges."""
    return {"status": "SUCCESS", "parameters": get_default_fcst_parameters()}, 200


@app.post('/get-fcst-train-ids')
async def get_fcst_train(user_id: int = Form(...), train_type: str = Form(...)):
    """List train_ids eligible for forecasting (new vs. re-run) for a user."""
    if verify_user_id(user_id):
        train_id = get_fcst_train_ids(train_type, user_id)
        return {"status": "SUCCESS", "train_id": train_id}, 200
    else:
        return {"status": "FAILURE", "message": "User not verified"}, 400


@app.post('/trigger-forecasting')
async def trigger_fcst(background_tasks: BackgroundTasks, user_id: int = Form(...), train_id: int = Form(...), parameters: str = Form(...), train_type: str = Form(...)):
    """Persist parameters and run the forecasting pipeline in the background.

    train_type 'create' uses the given train_id; 'existing' clones it to a new run.
    """
    if verify_user_id(user_id):
        if train_type == "create":
            insert_train_parameters_to_db(train_id, parameters)
            background_tasks.add_task(forecasting_pipeline, train_id)
        elif train_type == "existing":
            new_train_id = copy_existing_fcst_data_id(train_id)
            insert_train_parameters_to_db(new_train_id, parameters)
            background_tasks.add_task(forecasting_pipeline, new_train_id)
        return {"status": "SUCCESS", "message": "Forecasting triggered"}, 200
    else:
        return {"status": "FAILURE", "message": "User not verified"}, 400


@app.post('/trigger-metrics-calculation')
async def trigger_metric_calculation(user_id: int = Form(...), train_id: int = Form(...)):
    """Compute performance metrics for a run, unless they already exist (runs inline)."""
    if verify_user_id(user_id):
        if not verify_metrics_exists(train_id):
            calculate_metric(train_id)
            return {"status": "SUCCESS", "message": "Metrics calculation completed"}, 200
        else:
            return {"status": "FAILURE", "message": "Metrics already calculated"}, 400
    else:
        return {"status": "FAILURE", "message": "User not verified"}, 400


@app.post('/status')
async def fetch_run_status(user_id: int = Form(...)):
    """Return the run history (stage phases, statuses, timings) for a user."""
    if verify_user_id(user_id):
        data = get_train_history(user_id)
        return {"status": "SUCCESS", "data": data}, 200
    else:
        return {"status": "FAILURE", "message": "User not verified"}, 400
