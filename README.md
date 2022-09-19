# airspaced - a REST API to OpenAIP information

airspaced provides a lat x lon lookup to applicable airspaces
capable of offline operation
runs off a local spatialite database

example queries:

curl -X 'GET'   http://127.0.0.1:1815/
curl -X 'GET'   http://127.0.0.1:1815/v1/airspaces/47.1292371/15.2120164/7100
curl -X 'GET'   http://127.0.0.1:1815/v1/airspaces/47.1292371/15.2120164


## API docs

http://127.0.0.1:1815/docs

### OpenAPI description
http://127.0.0.1:1815/openapi.json

## requirements
apt-get install sqlite3 libsqlite3-dev libsqlite3-mod-spatialite
pip install "fastapi[all]"
pip install "uvicorn[standard]"
pip install geojson
pip install geojson-to-sqlite

## building the database

retrieve the GeoJson files relevant for your region (see  https://groups.google.com/g/openaip/c/srK1GeiVNPM for an explanation)

Example: Airspace for Austria and some neighbouring countries
`cd geojson-samples/`
`wget https://storage.googleapis.com/29f98e10-a489-4c82-ae5e-489dbcd4912f/at_asp.geojson`
`wget https://storage.googleapis.com/29f98e10-a489-4c82-ae5e-489dbcd4912f/si_asp.geojson`
`wget https://storage.googleapis.com/29f98e10-a489-4c82-ae5e-489dbcd4912f/ch_asp.geojson`
`wget https://storage.googleapis.com/29f98e10-a489-4c82-ae5e-489dbcd4912f/it_asp.geojson`
`wget https://storage.googleapis.com/29f98e10-a489-4c82-ae5e-489dbcd4912f/de_asp.geojson`

Convert to spatialite database - see https://pypi.org/project/geojson-to-sqlite/ :

`geojson-to-sqlite  --pk '' --properties --spatialite  --spatialite_mod=/usr/lib/x86_64-linux-gnu/mod_spatialite.so  --spatial-index  airspaces.db features  geojson-samples/??_asp.geojson`


NB: airspace geojson features files from OpenAIP have overlapping "id" properties, which means you cannot use them as primary key
the above statement works without a primary key which means you cannot upsert files - the whole database must be recreated.
## try out the database

`sqlite3 airspaces.db`
`sqlite> .load '/usr/lib/x86_64-linux-gnu/mod_spatialite.so'`

`sqlite>                 select properties from features where MBRWithin(ST_Point(15,47), geometry) and  ST_Within(ST_Point(15,47),geometry) limit 1;
{"_id": "6319941cd9f1e6a2b5f8ddeb", "approved": true, "name": "CTA S", "type": 0, "icaoClass": 3, "activity": 0, "onDemand": false, "onRequest": false, "byNotam": false, "specialAgreement": false, "country": "AT", "upperLimit": {"value": 195, "unit": 6, "referenceDatum": 2}, "lowerLimit": {"value": 9500, "unit": 1, "referenceDatum": 1}, "createdAt": "2022-09-08T07:05:00.185Z", "updatedAt": "2022-09-08T07:05:00.199Z", "createdBy": "OPONcQnzWGOLiJSceNaf8pvx1fA2", "updatedBy": "OPONcQnzWGOLiJSceNaf8pvx1fA2"}`


## running the service

### testing
adapt pathnames in app.py

`uvicorn app:app  --reload --port 1815`


## nginx proxy

TBD

## systemd service


TBD

