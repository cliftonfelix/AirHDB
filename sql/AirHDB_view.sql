DROP VIEW IF EXISTS hdb_listings;

CREATE VIEW hdb_listings AS
SELECT *
FROM hdb_units
WHERE can_book = 'Yes';