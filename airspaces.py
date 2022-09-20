import geojson
import json
import sqlite3
import uuid

# function that makes query results return lists of dictionaries instead of lists of tuples
def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def read_file(name):
    with open(name, "rb") as f:
        return f.read()


def read_json_file(name, asGeojson=False, object_hook=None):
    s = read_file(name).decode()
    if asGeojson:
        return geojson.loads(s, object_hook=object_hook)
    else:
        return json.loads(s, object_hook=object_hook)


def get_all_keys(d):
    for key, value in d.items():
        yield d, key
        if isinstance(value, dict):
            yield from get_all_keys(value)


def fixup(row, schema):
    for d, k in get_all_keys(row):
        if k in schema:
            d[k] = schema[k][d[k]]
    return row


class Airspaces:
    def __init__(self, mbtiles="", schema=None, spatialite=None):
        self.conn = sqlite3.connect(mbtiles)
        self.conn.enable_load_extension(True)
        self.conn.execute("SELECT load_extension(?)", [spatialite])

        # apply the function to the sqlite3 engine
        self.conn.row_factory = dict_factory
        self.cursor = self.conn.cursor()
        self.schema = read_json_file(
            schema,
            object_hook=lambda d: {
                int(k) if k.isnumeric() else k: v for k, v in d.items()
            },
        )

    def lookup(self, lat, lon, alt=None, shapes=False):
        query = (
            f"select properties, AsGeoJSON(geometry) from features "
            f"where MBRWithin(ST_Point({lon},{lat}), geometry) and  "
            f"ST_Within(ST_Point({lon},{lat}),geometry)"
        )
        self.cursor.execute(query)
        data = self.cursor.fetchall()

        if alt:
            response = {
                "within": {"type": "FeatureCollection", "features": []},
                "above": {"type": "FeatureCollection", "features": []},
                "below": {"type": "FeatureCollection", "features": []},
            }
        else:
            response = {"applicable": {"type": "FeatureCollection", "features": []}}

        # create a new list which will store the single GeoJSON features
        #featureCollection = list()

        for row in data:
            # create a single GeoJSON geometry from the geometry column which already contains a GeoJSON string
            geom = geojson.loads(row["AsGeoJSON(geometry)"])

            # remove the geometry field from the current's row's dictionary
            row.pop("AsGeoJSON(geometry)")

            # create a new GeoJSON feature and pass the geometry columns as well as all remaining attributes which are stored in the row dictionary
            j = json.loads(row["properties"])
            props = fixup(j, self.schema)

            asp = geojson.Feature(geometry=geom, properties=props, id=props["_id"])

            # append the current feature to the list of all features
            #featureCollection.append(asp)

            if alt:
                (
                    above_lower_boundary,
                    below_upper_boundary,
                ) = self.test_current_airspace(props, alt)
                if above_lower_boundary and below_upper_boundary:
                    response["within"]["features"].append(asp)
                elif above_lower_boundary:
                    response["above"]["features"].append(asp)
                elif below_upper_boundary:
                    response["below"]["features"].append(asp)

                # print("lookup", alt, above_lower_boundary, below_upper_boundary, props["lowerLimit"], props["upperLimit"])
            else:
                response["applicable"]["features"].append(props)

        # add the query as point feature
        # response["query"] = geojson.Feature(
        #     geometry=geojson.Point((lon, lat, alt)),
        #     id=uuid.uuid4(),
        # )

        #return {"type": "FeatureCollection", "features": featureCollection}
        return  response

    def within_airspace(self, altitude_ft, upper, upper_unit, lower, lower_unit):
        fl = int(altitude_ft / 100)
        below_upper_boundary = False
        above_lower_boundary = False
        if upper_unit == "Feet":
            below_upper_boundary = altitude_ft < upper
        if upper_unit == "Flight Level":
            below_upper_boundary = fl < upper

        if lower_unit == "Feet":
            above_lower_boundary = altitude_ft > lower
        if lower_unit == "Flight Level":
            above_lower_boundary = fl > lower
        return (above_lower_boundary, below_upper_boundary)

    def test_current_airspace(self, feature, altitude_ft):
        try:
            upper = feature["upperLimit"]["value"]
            upper_unit = feature["upperLimit"]["unit"]
            # upper_ref = feature["upperLimit"]["referenceDatum"]
            lower = feature["lowerLimit"]["value"]
            lower_unit = feature["lowerLimit"]["unit"]
            # lower_ref = feature["lowerLimit"]["referenceDatum"]
        except Exception:
            return (False, False)
        return self.within_airspace(altitude_ft, upper, upper_unit, lower, lower_unit)
