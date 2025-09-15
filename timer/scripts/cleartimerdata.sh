#!/bin/zsh

# Define the database credentials
DB_NAME="rfid_system"
DB_USER="postgres"
DB_PASSWORD="r0ckkrush3r"
TABLE_NAME="timeresults"

# Safety confirmation prompt
echo "WARNING: This will permanently delete ALL data from table: $TABLE_NAME"
echo "This action cannot be undone!"
echo ""
echo "To proceed, type exactly: DELETE DATA"
read -r user_input

# Check if user typed the exact confirmation phrase
if [ "$user_input" != "DELETE DATA" ]; then
  echo "Confirmation failed. Operation cancelled."
  echo "You must type exactly: DELETE DATA"
  exit 1
fi

echo ""
echo "Confirmation received. Proceeding with table truncation..."

# Truncate the table
echo "Truncating table: $TABLE_NAME"
PGPASSWORD=$DB_PASSWORD psql -U $DB_USER -d $DB_NAME -c "TRUNCATE TABLE $TABLE_NAME RESTART IDENTITY;"

# Check if the truncate was successful
if [ $? -eq 0 ]; then
  echo "Table truncation successful: $TABLE_NAME"
  echo "All data removed, table ready for new data"
else
  echo "Table truncation failed"
  exit 1
fi
