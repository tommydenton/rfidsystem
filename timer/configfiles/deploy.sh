#!/bin/zsh


# Copy the files from the source to the target directory
echo "Copying files from $SOURCE_DIR to $TARGET_DIR..."
sudo cp -R /home/pi//rfidsystem/timer/*  /var/www/html/timer

# Restart the services using PM2
echo "Restarting services..."
pm2 restart /var/www/html/timer/ntpapi/ntpapi.mjs
pm2 restart /var/www/html/timer/display/server.js

# Check the Git status
#echo "Checking Git status..."
#git -C /home/pi/html/rfidsystem/timer status

echo "Deployment completed."

