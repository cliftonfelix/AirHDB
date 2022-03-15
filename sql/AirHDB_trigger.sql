DROP TRIGGER IF EXISTS insert_nearest_mrt;

CREATE TRIGGER insert_nearest_mrt
BEFORE INSERT OR UPDATE ON hdb_units
FOR EACH ROW EXECUTE PROCEDURE find_nearest_mrt();