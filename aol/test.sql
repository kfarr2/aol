/*
This the the inital SQL needed to run tests
*/
CREATE SCHEMA mussels;
CREATE TABLE mussels.display_view (
    id integer PRIMARY KEY,
    substrate_type VARCHAR(255),
    status VARCHAR(255),
    waterbody_name VARCHAR(255),
    physical_description VARCHAR(255),
    date_checked TIMESTAMP,
    status_id INTEGER,
    agency VARCHAR(255)
);
SELECT AddGeometryColumn('mussels', 'display_view', 'the_geom', 4326, 'POINT', 2);
