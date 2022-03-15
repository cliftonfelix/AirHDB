DROP TABLE IF EXISTS bookings;
DROP TABLE IF EXISTS hdb_units;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS towns;
DROP TABLE IF EXISTS mrt_stations;
DROP TABLE IF EXISTS hdb_types_info;

CREATE TABLE IF NOT EXISTS towns (
	town VARCHAR(256) PRIMARY KEY,
	region VARCHAR(256)
);

CREATE TABLE IF NOT EXISTS mrt_stations (
	mrt_name VARCHAR(256) PRIMARY KEY,
	mrt_lat NUMERIC,
	mrt_long NUMERIC
);

CREATE TABLE IF NOT EXISTS hdb_types_info (
	hdb_type VARCHAR(256) PRIMARY KEY,
	number_of_bedrooms INT,
	number_of_bathrooms INT,
	max_occupants INT
);

CREATE TABLE IF NOT EXISTS hdb_units (
	hdb_address VARCHAR(256) NOT NULL,
	hdb_unit_number VARCHAR(256) NOT NULL CHECK (hdb_unit_number LIKE '#%-%'), -- More constraint?
	hdb_type VARCHAR(256) NOT NULL REFERENCES hdb_types_info(hdb_type),
	size INT NOT NULL,
	price_per_day NUMERIC NOT NULL CHECK (price_per_day >= 0),
	town VARCHAR(256) NOT NULL REFERENCES towns(town),
	multistorey_carpark VARCHAR(3) NOT NULL CHECK(multistorey_carpark = 'Yes' OR 
												  multistorey_carpark = 'No'),
	contact_person_name VARCHAR(256) NOT NULL,
	contact_person_mobile INT NOT NULL CHECK ((contact_person_mobile BETWEEN 30000000 AND 39999999) OR
											  (contact_person_mobile BETWEEN 60000000 AND 69999999) OR
											  (contact_person_mobile BETWEEN 80000000 AND 89999999) OR
											  (contact_person_mobile BETWEEN 90000000 AND 98999999)), -- https://en.wikipedia.org/wiki/Telephone_numbers_in_Singapore
	hdb_lat NUMERIC NOT NULL CHECK (hdb_lat BETWEEN 1.158 AND 1.472), -- Can we find a tighter constraint for Singapore latitude?
	hdb_long NUMERIC NOT NULL CHECK (hdb_long BETWEEN 103.6 AND 104.1), -- Can we find a tighter constraint for Singapore longitude?
	nearest_mrt VARCHAR(256) NOT NULL,
	PRIMARY KEY (hdb_address, hdb_unit_number), -- Other alternatives?
	CHECK ((hdb_type = '2-Room/2-Room Flexi' AND ((size BETWEEN 35 AND 38) OR (size BETWEEN 45 AND 47))) OR
		   (hdb_type = '3-Room' AND (size BETWEEN 60 AND 68)) OR
		   (hdb_type = '4-Room' AND (size BETWEEN 85 AND 93)) OR
		   (hdb_type = '5-Room' AND (size BETWEEN 107 AND 113)) OR
		   (hdb_type = '3-Gen' AND (size BETWEEN 115 AND 118))) -- https://www.hdb.gov.sg/residential/buying-a-flat/new/types-of-flats
);

CREATE TABLE IF NOT EXISTS users (
	name VARCHAR(256) NOT NULL,
	email_address VARCHAR(256) PRIMARY KEY CHECK (email_address LIKE '%_@_%._%'),
	password VARCHAR(256) NOT NULL,
	mobile_number INT NOT NULL CHECK ((mobile_number BETWEEN 30000000 AND 39999999) OR
									  (mobile_number BETWEEN 60000000 AND 69999999) OR
									  (mobile_number BETWEEN 80000000 AND 89999999) OR
									  (mobile_number BETWEEN 90000000 AND 98999999)), -- https://en.wikipedia.org/wiki/Telephone_numbers_in_Singapore
	is_admin VARCHAR(3) NOT NULL DEFAULT 'No' CHECK(is_admin = 'Yes' OR
												    is_admin = 'No')
);

CREATE TABLE IF NOT EXISTS bookings (
	hdb_address VARCHAR(256) NOT NULL,
	hdb_unit_number VARCHAR(256) NOT NULL,
	booked_by VARCHAR(256) NOT NULL CHECK (booked_by LIKE '%_@_%._%') REFERENCES users(email_address),
	start_date DATE NOT NULL CHECK (start_date >= '2022-04-11'), -- Initial start date 11 April
	end_date DATE NOT NULL, -- End date is like the checkout date. A new booking can start on the end date.
	credit_card_type VARCHAR(256) NOT NULL,
	credit_card_number VARCHAR(16) NOT NULL,
	total_price NUMERIC NOT NULL,
	PRIMARY KEY (hdb_address, hdb_unit_number, booked_by, start_date, end_date),
	FOREIGN KEY (hdb_address, hdb_unit_number) REFERENCES hdb_units(hdb_address, hdb_unit_number),
	CHECK (end_date > start_date),
	CHECK((credit_card_type = 'visa' 
		   AND LEFT(credit_card_number, 1) = '4'
		   AND (LENGTH(credit_card_number) IN (13, 16)))
		  OR (credit_card_type = 'mastercard' 
			  AND LENGTH(credit_card_number) = 16
			  AND (LEFT(credit_card_number, 4) BETWEEN '2221' AND '2720' 
				   OR LEFT(credit_card_number, 2) BETWEEN '50' AND '55'))
		  OR (credit_card_type = 'americanexpress' 
			  AND LENGTH(credit_card_number) = 15
			  AND (LEFT(credit_card_number, 2) IN ('33', '34', '37'))))
	-- Source: Wikipedia and some other sites
	-- by right, mastercard doesn't include 50 and americanexpress doesn't include 33, but sample data from Mockaroo include them.
	-- sample data from Mockaroo also doesnt include mastercard with starting numbers 2221 to 2720.
);
