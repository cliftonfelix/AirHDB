-- COPY towns
-- FROM 'D:\NUS\FILE\Y2S2\IT2002\Project\AirHDB/towns.csv' -- CHANGE PATH in Github
-- Heroku
\COPY towns FROM 'cliftonfelix/AirHDB/sql/Data/towns.csv' DELIMITER ',' CSV HEADER;

-- COPY mrt_stations
-- FROM 'D:\NUS\FILE\Y2S2\IT2002\Project\AirHDB/mrt_stations.csv' -- CHANGE PATH in Github
\COPY mrt_stations FROM 'cliftonfelix/AirHDB/sql/Data/mrt_stations.csv' DELIMITER ',' CSV HEADER;

-- COPY hdb_types_info
-- FROM 'D:\NUS\FILE\Y2S2\IT2002\Project\AirHDB/hdb_types_info.csv' -- CHANGE PATH in Github
\COPY hdb_types_info FROM 'cliftonfelix/AirHDB/sql/Data/hdb_types_info.csv' DELIMITER ',' CSV HEADER;

INSERT INTO hdb_units VALUES ('test_name', '252, YISHUN RING ROAD', '#07-91', '3-Room', 63, 100, 'Yishun', 'No', 'Hari', '90233232', 
 							 1.434725, 103.841021); -- TESTING ONLY
INSERT INTO hdb_units VALUES ('test_name', '872A, TAMPINES ST 86', '#07-91', '3-Room', 63, 100, 'Tampines', 'No', 'Hari', '90233232', 
 							 1.355485, 103.930827); -- TESTING ONLY
							 
INSERT INTO users VALUES ('Admin', 'admin@airhdb.com', 'AirHDB_admin', '92450330', 'Yes'); -- TESTING ONLY
INSERT INTO users VALUES ('Bryan Tan', 'btan@u.nus.edu', '12345678', '82342321'); -- TESTING ONLY

INSERT INTO bookings VALUES ('252, YISHUN RING ROAD', '#07-91', 'btan@u.nus.edu', 
							 '2022-04-11', '2022-04-18', 'mastercard', '5100170545952128', 325.68); -- TESTING ONLY
INSERT INTO bookings VALUES ('872A, TAMPINES ST 86', '#07-91', 'btan@u.nus.edu',
							 '2022-04-14', '2022-04-19', 'mastercard', '5100170545952128', 325.68); -- TESTING ONLY
INSERT INTO bookings VALUES ('252, YISHUN RING ROAD', '#07-91', 'btan@u.nus.edu', 
							 '2022-04-25', '2022-04-27', 'mastercard', '5100170545952128', 325.68); -- TESTING ONLY
