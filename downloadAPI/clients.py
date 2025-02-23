from multiprocessing import Process
from time import perf_counter
import time
import requests
import numpy as np
import json


def send_req(i, return_dict):
    datatype = ("star", "visit")[np.random.randint(0, 1)]
    if datatype == "star":
        dataset = ("spall", "aspcap", "best",
                   "thepayne")[np.random.randint(0, 3)]
    else:
        dataset = ("spall", "thepayne")[np.random.randint(0, 1)]
    expression = ("", "g_mag < 17",
                  "xcsao_teff < 9e3")[np.random.randint(0, 3)]
    if (dataset != "spall") and (expression == "xcsao_teff < 9e3"):
        expression = (
            expression,
            "((teff < 9e3)&(logg < 2))",
            "((teff < 9e3) & (logg > 4))",
        )[np.random.randint(0, 2)]
    carton = ([], ["mwm_yso_pms"], ["mwm_halo_local",
                                    "bhm_aqmes"])[np.random.randint(0, 3)]
    mapper = ([], ["mwm"], ["mwm", "bhm"])[np.random.randint(0, 3)]
    flags = ("", "purely non-flagged",
             "purely non-flagged,sdss5 only")[np.random.randint(0, 2)]
    params = dict(expression=expression,
                  carton=carton,
                  mapper=mapper,
                  flags=flags)
    start = perf_counter()
    resp = requests.post(
        f"http://localhost:8000/filter_subset/ipl3/{datatype}/{dataset}",
        json=params)
    print(f"Got response in  {perf_counter() - start}s")
    return_dict[i] = resp


if __name__ == "__main__":
    return_dict = {}
    while True:
        processes = [
            Process(target=send_req, args=(i, return_dict)) for i in range(5)
        ]
        for i in range(5):
            processes[i].start()
            print(f"Started process {i}")
        time.sleep(30)
