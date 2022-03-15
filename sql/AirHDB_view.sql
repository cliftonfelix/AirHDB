DROP VIEW IF EXISTS hdb_listings;

CREATE VIEW hdb_listings AS
SELECT hdb1.*, 
	   CASE
	   		WHEN get_distance(hdb1.hdb_lat, hdb1.hdb_long, mrt1.mrt_lat, mrt1.mrt_long) < 1 
			THEN CONCAT(mrt1.mrt_name, ' (', (get_distance(hdb1.hdb_lat, hdb1.hdb_long, mrt1.mrt_lat, mrt1.mrt_long) * 1000) :: INT, ' m)')
			ELSE CONCAT(mrt1.mrt_name, ' (', ROUND(get_distance(hdb1.hdb_lat, hdb1.hdb_long, mrt1.mrt_lat, mrt1.mrt_long) :: NUMERIC, 2)
						, ' km)')
	   END nearest_mrt
FROM hdb_units hdb1, mrt_stations mrt1
WHERE get_distance(hdb1.hdb_lat, hdb1.hdb_long, mrt1.mrt_lat, mrt1.mrt_long) = 
	  (SELECT MIN(get_distance(hdb2.hdb_lat, hdb2.hdb_long, mrt2.mrt_lat, mrt2.mrt_long))
	   FROM hdb_units hdb2, mrt_stations mrt2
	   WHERE hdb1.hdb_address = hdb2.hdb_address AND hdb1.hdb_unit_number = hdb2.hdb_unit_number
	   GROUP BY hdb2.hdb_address, hdb2.hdb_unit_number);
	   
SELECT *
FROM hdb_listings;