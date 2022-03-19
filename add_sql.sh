# Construct the URI from the .env
DB_HOST=''
DB_NAME=''
DB_USER=''
DB_PORT=''
DB_PASSWORD=''

while IFS= read -r line
do
  if [[ $line == DB_HOST* ]]
  then
    DB_HOST=$(cut -d "=" -f2- <<< $line | tr -d \')
  elif [[ $line == DB_NAME* ]]
  then
    DB_NAME=$(cut -d "=" -f2- <<< $line | tr -d \' )
  elif [[ $line == DB_USER* ]]
  then
    DB_USER=$(cut -d "=" -f2- <<< $line | tr -d \' )
  elif [[ $line == DB_PORT* ]]
  then
    DB_PORT=$(cut -d "=" -f2- <<< $line | tr -d \')
  elif [[ $line == DB_PASSWORD* ]]
  then
    DB_PASSWORD=$(cut -d "=" -f2- <<< $line | tr -d \')
  fi
done < ".env"

URI="postgres://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"

# Run the scripts to insert data.
psql ${URI} -f sql/AirHDB_schema.sql
psql ${URI} -f sql/AirHDB_function.sql
psql ${URI} -f sql/AirHDB_trigger.sql
psql ${URI} -f sql/AirHDB_populate_hdb_types_info.sql
psql ${URI} -f sql/AirHDB_populate_mrt_stations.sql
psql ${URI} -f sql/AirHDB_populate_towns.sql
psql ${URI} -f sql/AirHDB_populate_hdb_units.sql
psql ${URI} -f sql/AirHDB_populate_users.sql
psql ${URI} -f sql/AirHDB_populate_bookings.sql
psql ${URI} -f sql/AirHDB_view.sql
