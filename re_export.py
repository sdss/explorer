from astropy.table import Table
import sys

sys.path.insert(0, "/home/riley/uni/archive/2023/s2/phs2360/code")
from cleaners import clean_APOGEE

t = Table.read(
    "/home/riley/uni/archive/2023/s2/phs2360/data/allApogeeNetStar-0.4.0.fits"
).to_pandas()
t = clean_APOGEE(t)
t.to_parquet("/home/riley/uni/rproj/data/allApogeeNetStar-0.4.0.parquet")
