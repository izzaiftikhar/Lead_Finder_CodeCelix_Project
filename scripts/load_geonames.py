"""Load GeoNames cities15000.txt (CC-BY 4.0, attribution required) for the 7 supported countries.
Usage: python scripts/load_geonames.py path/to/cities15000.txt   (admin1 here is the GeoNames admin1 code)"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from backend.core import db, schema
from backend.core.seed_data import COUNTRIES


def load(path):
    schema.init_db()
    n = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) < 15 or p[8] not in COUNTRIES:
                continue
            name, lat, lng, cc, admin1, pop = p[1], p[4], p[5], p[8], p[10], p[14]
            if db.one("SELECT 1 AS x FROM cities WHERE country=? AND name=?", (cc, name)):
                continue
            db.execute("INSERT INTO cities(country,admin1,name,lat,lng,population) VALUES(?,?,?,?,?,?)",
                       (cc, admin1 or None, name, float(lat), float(lng), int(pop or 0)))
            n += 1
    return n


if __name__ == "__main__":
    print("loaded", load(sys.argv[1]), "cities")
