"""Miscellaneous test functions. Not implemented fully yet."""

from multiprocessing import Process
from time import perf_counter
import time
import requests
import numpy as np
import json
from fastapi.testclient import TestClient

from .main import app

client = TestClient(app)


def send_req(params):
    print("sending", params)
    datatype = params["datatype"]
    dataset = params["dataset"]
    start = perf_counter()
    resp = requests.post(
        f"http://localhost:8000/filter_subset/ipl3/{datatype}/{dataset}",
        params=params,
        data=json.dumps(params),
    )
    # print("dataset", dataset)
    # print("datatype", datatype)
    # for k, v in params.items():
    #    print(k, v)
    print(f"Got response in  {perf_counter() - start}s")
    print("status", resp.status_code)
    print("uuid:", json.loads(resp.text)["uid"])


def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"This is": "Explorer server"}


# if __name__ == "__main__":
#    while True:
#        for i in range(5):
#            datatype = ("star", "visit")[np.random.randint(0, 1)]
#            if datatype == "star":
#                dataset = ("spall", "aspcap", "best",
#                           "thepayne")[np.random.randint(0, 3)]
#            else:
#                dataset = ("spall", "thepayne")[np.random.randint(0, 1)]
#            expression = ("", "g_mag < 17",
#                          "xcsao_teff < 9e3")[np.random.randint(0, 3)]
#            if (dataset != "spall") and (expression == "xcsao_teff < 9e3"):
#                expression = (
#                    expression,
#                    "teff < 9e3 &  logg < 2",
#                    "teff < 12e3 & logg > 4",
#                )[np.random.randint(0, 2)]
#            if np.random.randint(0, 1):
#                carton = ([], ["mwm_yso_pms"], ["mwm_halo_local", "bhm_aqmes"
#                                                ])[np.random.randint(0, 3)]
#                mapper = []
#            else:
#                mapper = ([], ["mwm"], ["mwm", "bhm"])[np.random.randint(0, 3)]
#                carton = []
#            flags = ("", "purely non-flagged",
#                     "purely non-flagged,sdss5 only")[np.random.randint(0, 2)]
#            params = dict(expression=expression,
#                          carton=carton,
#                          mapper=mapper,
#                          flags=flags)
#            p = Process(target=send_req, args=(params, ))
#            p.start()
#            print(f"Started process {i}", )
#        time.sleep(20)
