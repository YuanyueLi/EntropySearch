#!/usr/bin/env python3
import sys
import base64
import copy
import datetime
import json
import multiprocessing
from typing import Annotated, Union

import numpy as np
import uvicorn
from entropy_search import EntropySearch
from fastapi import BackgroundTasks, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

########################################################################################################################
# Entropy search
entropy_search_worker = None
search_parameters = None


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, set):
            return list(obj)
        elif isinstance(obj, bytes):
            return base64.b64encode(obj).decode("utf-8")
        elif isinstance(obj, datetime.datetime):
            return obj.isoformat()
        elif np.isnan(obj):
            return None
        return super(NumpyEncoder, self).default(obj)


########################################################################################################################
# Send parameters to start searching
class InfoForEntropySearch(BaseModel):
    file_query: str = ""
    file_library: str = ""
    path_output: str = ""

    ms1_tolerance_in_da: float = 0.01
    ms2_tolerance_in_da: float = 0.02
    top_n: int = 100
    cores: int = 1


def run_entropy_search(info: dict):
    print(info)
    global search_parameters
    search_parameters = info.copy()
    print("Start searching")
    global entropy_search_worker
    entropy_search_worker = EntropySearch(info["ms2_tolerance_in_da"])
    entropy_search_worker.load_spectral_library(info["file_library"])
    entropy_search_worker.search_file(info["file_query"], info["top_n"], info["ms1_tolerance_in_da"], info["ms2_tolerance_in_da"], info["cores"])
    print("Finish searching")
    return None


@app.post("/entropy_search")
async def entropy_search_worker(info: InfoForEntropySearch, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_entropy_search, info.dict())
    return {"file_query": info.file_query}


########################################################################################################################
# Get one spectrum result
@app.get("/get/one_spectrum/{scan}")
async def get_one_spectrum(scan: int):
    try:
        return json.loads(json.dumps(entropy_search_worker.get_one_spectrum_result(
            scan, search_parameters["top_n"], search_parameters["ms1_tolerance_in_da"], search_parameters["ms2_tolerance_in_da"]), cls=NumpyEncoder))
    except Exception as e:
        return []


# Get one library spectrum
@app.get("/get/one_library_spectrum/{charge}/{idx}")
async def get_one_library_spectrum(charge: int, idx: int):
    try:
        return json.loads(json.dumps(entropy_search_worker.get_one_library_spectrum(charge, idx), cls=NumpyEncoder))
    except:
        return []


# Get all spectra
@app.get("/get/all_spectra")
async def get_all_spectra():
    try:
        all_spectra = entropy_search_worker.all_spectra
        result = []
        for i, spec in enumerate(all_spectra):
            spec = copy.copy(spec)
            if len(spec.pop("peaks", [])) == 0:
                continue
            spec.pop("identity_search", None)
            spec.pop("open_search", None)
            spec.pop("neutral_loss_search", None)
            spec.pop("hybrid_search", None)
            result.append(spec)

        return json.loads(json.dumps(result, cls=NumpyEncoder))
    except:
        return []


# Get searching status
@app.get("/get/status")
async def get_status():
    try:
        return {"status": entropy_search_worker.status,
                "is_ready": entropy_search_worker.ready,
                "is_finished": entropy_search_worker.finished}
    except:
        return {"status": "not started",
                "is_ready": False,
                "is_finished": False}


# Get maximum cpu cores
@app.get("/get/cpu")
async def get_cpu():
    try:
        return {"cpu": multiprocessing.cpu_count()}
    except:
        return {"cpu": 1}


########################################################################################################################


@app.get("/")
async def read_root():
    return {"Hello": "World"}


if __name__ == "__main__":    
    if sys.platform.startswith('win'):
        # On Windows calling this function is necessary.
        multiprocessing.freeze_support()

    uvicorn.run(app, host="localhost", port=8711)
