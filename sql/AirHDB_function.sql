CREATE OR REPLACE FUNCTION get_distance(
	hdb_lat NUMERIC,
	hdb_long NUMERIC,
	mrt_lat NUMERIC,
	mrt_long NUMERIC
)
RETURNS NUMERIC
language plpgsql
AS
$$
BEGIN
	RETURN (12742 * ASIN(SQRT(0.5 - COS((mrt_lat - hdb_lat) * PI() / 180) / 2 + 
							  COS(hdb_lat * PI() / 180) * COS(mrt_lat * PI() / 180) *
							  (1 - COS((mrt_long - hdb_long) * PI() / 180)) / 2)));
END;
$$;

CREATE OR REPLACE FUNCTION find_nearest_mrt()
RETURNS TRIGGER
LANGUAGE plpgsql
AS 
$$
BEGIN
	NEW.nearest_mrt := 
	(SELECT CASE
		WHEN get_distance(NEW.hdb_lat, NEW.hdb_long, mrt1.mrt_lat, mrt1.mrt_long) < 1 
			THEN CONCAT(mrt1.mrt_name, ' (', (get_distance(NEW.hdb_lat, NEW.hdb_long, mrt1.mrt_lat, mrt1.mrt_long) * 1000) :: INT, ' m)')
		ELSE CONCAT(mrt1.mrt_name, ' (', ROUND(get_distance(NEW.hdb_lat, NEW.hdb_long, mrt1.mrt_lat, mrt1.mrt_long) :: NUMERIC, 2), ' km)')
	END nearest
	FROM mrt_stations mrt1
	ORDER BY get_distance(NEW.hdb_lat, NEW.hdb_long, mrt1.mrt_lat, mrt1.mrt_long) ASC
	LIMIT 1);
	RETURN NEW;
END;
$$;
