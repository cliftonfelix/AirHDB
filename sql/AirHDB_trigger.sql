DROP TRIGGER IF EXISTS insert_nearest_mrt ON hdb_units;
DROP TRIGGER IF EXISTS new_total_price ON bookings;
DROP TRIGGER IF EXISTS booking_dates_availability ON bookings;
DROP TRIGGER IF EXISTS new_mrt_station ON mrt_stations;

CREATE TRIGGER insert_nearest_mrt
BEFORE INSERT OR UPDATE ON hdb_units
FOR EACH ROW EXECUTE PROCEDURE find_nearest_mrt();

CREATE TRIGGER new_total_price
BEFORE UPDATE ON bookings
FOR EACH ROW EXECUTE PROCEDURE change_total_price();

CREATE TRIGGER booking_dates_availability
BEFORE INSERT OR UPDATE ON bookings
FOR EACH ROW EXECUTE PROCEDURE check_dates_availability();

CREATE TRIGGER new_mrt_station
AFTER INSERT ON mrt_stations
FOR EACH ROW EXECUTE PROCEDURE update_all_nearest_mrts();
