# AirHDB
AirHDB IT2002 Project

**Description**

An accommodation sharing platform for HDB units renting in Singapore. HDB owners and real estate agents can submit any post request to the administrator. Administrator can view, edit, add, and delete the HDB unit listing on the Admin Page. Users can look through the HDB units on the Listings Page. On this page, users can search for the available HDB units to rent based on the dates, number of guests, and some other filters. They can also book the units. When booking the units, users need to input their credit card type and number. Successful booking will be added to the database.

When opening the app, users will be directed to the login page where they can register and login. Logging in with an administrator account will be directed to the Admin Page, while logging in with the normal account will be directed to the Listings Page. 


**Data Source**
https://data.gov.sg/dataset/hdb-property-information (some columns in hdb_units)
https://mockaroo.com (some columns in hdb_units, bookings, users)
https://www.kaggle.com/yxlee245/singapore-train-station-coordinates (mrt_stations)
https://en.wikipedia.org/wiki/Planning_Areas_of_Singapore (towns)
https://www.hdb.gov.sg/residential/buying-a-flat/new/types-of-flats (hdb_types_info and CHECK constraints for hdb_type and size in hdb_units)
https://www.hdb.gov.sg/cs/infoweb/about-us/news-and-publications/press-releases/revised-occupancy-cap-for-renting-out-hdb-flats#:~:text=From%201%20May%202018%2C%20the,persons%20and%204%20persons%20respectively. (hdb_types_info)

**Pages**
**User Login/Register Page**
The usual login/register page. The inputted email and password during login will be checked with the users table. A newly registered user data will be stored to users table. If the account is an admin account, it will redirected to Admin Page. If normal account, redirected to Listings Page.

**Admin Page**
A simple table with add, view, edit, and delete buttons (same as AppStore example) and a bookings table that shows all the bookings. There will only be 1 admin account.

**Listings Page**
Similar to Admin Page, but with several filters and a book button for each entry.
Filters: date, number of guests, price per day, HDB type, number of bedrooms, number of bathrooms, region, town, multistorey_carpark.
Design will be something similar to https://search.oakwood.com/

**Add Page**
A simple add page which is only accessible by the administrator.

**View Page**
A simple view page which is by both the administrator and users.

**Edit Page**
A simple edit page which is only accessible by the administrator. It will not show the hdb_lat, hdb_long, and nearest_mrt columns as the values for these columns will be computed in the backend. An edit to the hdb_units entry will trigger the SQL to update all entries of that unit in bookings based on the new data.

**Delete Page**
Delete page is only accessible by the administrator. A delete to the hdb_units entry will trigger the SQL to delete all entries of that unit in bookings.

**Book Page**
This page will be displayed after the users click the book button in Listings Page. The users will be prompted to input their credit card type and credit card number in this page. Successful bookings will be added to the bookings table.
