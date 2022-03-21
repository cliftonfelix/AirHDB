CREATE OR REPLACE FUNCTION get_distance(
	hdb_lat NUMERIC,
	hdb_long NUMERIC,
	mrt_lat NUMERIC,
	mrt_long NUMERIC
)
RETURNS NUMERIC
LANGUAGE plpgsql
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
	(SELECT mrt1.mrt_name
	FROM mrt_stations mrt1
	ORDER BY get_distance(NEW.hdb_lat, NEW.hdb_long, mrt1.mrt_lat, mrt1.mrt_long) ASC
	LIMIT 1);
	
	NEW.nearest_mrt_distance :=
	(SELECT ROUND(get_distance(NEW.hdb_lat, NEW.hdb_long, mrt1.mrt_lat, mrt1.mrt_long) :: NUMERIC, 2)
	FROM mrt_stations mrt1
	ORDER BY get_distance(NEW.hdb_lat, NEW.hdb_long, mrt1.mrt_lat, mrt1.mrt_long) ASC
	LIMIT 1);
	
	RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION change_total_price()
RETURNS TRIGGER
LANGUAGE plpgsql
AS 
$$
BEGIN
	NEW.total_price := 
	(SELECT (NEW.end_date - NEW.start_date) * (SELECT hu1.price_per_day
											   FROM hdb_units hu1
											   WHERE hu1.hdb_id = NEW.hdb_id));
	RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION check_dates_availability()
RETURNS TRIGGER
LANGUAGE plpgsql
AS 
$$
BEGIN
	IF EXISTS (SELECT *
			   FROM bookings b1
			   WHERE NEW.booking_id <> b1.booking_id AND
			   		 NEW.hdb_id = b1.hdb_id AND
			   		 ((NEW.start_date BETWEEN b1.start_date AND b1.end_date - 1 OR
			   		 NEW.end_date - 1 BETWEEN b1.start_date AND b1.end_date - 1) OR
			   		 (b1.start_date BETWEEN NEW.start_date AND NEW.end_date - 1 OR
			   		 b1.end_date - 1 BETWEEN NEW.start_date AND NEW.end_date - 1)))
		THEN RAISE EXCEPTION 'Booking Dates Not Available';
	ELSE
		RETURN NEW;
	END IF;
	RETURN NEW;
END;
$$;
