# uvicorn app:app --reload --port 1815

# curl -X 'GET'   http://127.0.0.1:1815/
# curl -X 'GET'   http://127.0.0.1:1815/v1/airspaces/47.1292371/15.2120164/7100
# curl -X 'GET'   http://127.0.0.1:1815/v1/airspaces/47.1292371/15.2120164

from typing import Union
import uvicorn
import logging
from fastapi import FastAPI
from pydantic import BaseModel

from airspaces import Airspaces

MBTILES = "./airspaces.db"
SCHEMA = "./schema.json"
SPATIALITE = "/usr/lib/x86_64-linux-gnu/mod_spatialite.so"

app = FastAPI()
airspaces = Airspaces(mbtiles=MBTILES, schema=SCHEMA, spatialite=SPATIALITE)


class Location(BaseModel):
    lat: float
    lon: float
    alt: Union[float, None] = None
    shapes: Union[bool, None] = None


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/v1/airspaces/")
async def lookup_location(item: Location):
    return airspaces.lookup(item.lat, item.lon, alt=item.alt, shapes=item.shapes)


@app.get("/v1/airspaces/{lat}/{lon}/{alt}")
@app.get("/v1/airspaces/{lat}/{lon}/{alt}/", include_in_schema=False)
async def read_pos(lat: float, lon: float, alt: float):
    return airspaces.lookup(lat, lon, alt=alt)


@app.get("/v1/airspaces/{lat}/{lon}")
@app.get("/v1/airspaces/{lat}/{lon}/", include_in_schema=False)
async def read_item(lat: float, lon: float):
    return airspaces.lookup(lat, lon)


if __name__ == "__main__":
    config = uvicorn.run("app", port=1815, log_level="debug")
    server = uvicorn.Server(config)
    server.run()
