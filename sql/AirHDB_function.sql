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
	RETURN ROUND((12742 * ASIN(SQRT(0.5 - COS((mrt_lat - hdb_lat) * PI() / 180) / 2 + 
							 		COS(hdb_lat * PI() / 180) * COS(mrt_lat * PI() / 180) *
									(1 - COS((mrt_long - hdb_long) * PI() / 180)) / 2)))::NUMERIC, 2);
END;
$$;