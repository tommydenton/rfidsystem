#!/bin/zsh

# Define the database credentials
DB_NAME="rfid_system"
DB_USER="postgres"
DB_PASSWORD="r0ckkrush3r"
TABLE_NAME="timeresults"

# Get the current timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Define the output file path
OUTPUT_FILE="/var/www/html/timer/exports/timeresults_${TIMESTAMP}.csv"

# Export the table to a CSV file
PGPASSWORD=$DB_PASSWORD psql -U $DB_USER -d $DB_NAME -c "\COPY $TABLE_NAME TO '$OUTPUT_FILE' WITH CSV HEADER"

# Check if the export was successful
if [ $? -eq 0 ]; then
  echo "Export successful: $OUTPUT_FILE"
else
  echo "Export failed"
fi
