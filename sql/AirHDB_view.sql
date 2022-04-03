DROP VIEW IF EXISTS hdb_listings;
DROP VIEW IF EXISTS refunds_details;

CREATE VIEW hdb_listings AS
SELECT *
FROM hdb_units hu1
NATURAL JOIN hdb_types_info hti1
NATURAL JOIN towns t1
WHERE can_book = 'Yes'
ORDER BY hdb_id;

CREATE VIEW refunds_details AS
SELECT *
FROM refunds
NATURAL JOIN bookings
ORDER BY booking_id;
