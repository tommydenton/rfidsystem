```markdown
# RFID Project Setup Guide

This guide outlines the steps to set up the environment for the RFID project on a Raspberry Pi running the Bullseye OS.

## Table of Contents

- [Environment Setup](#environment-setup)
- [Webserver Setup](#webserver-setup)
- [API Server Setup](#api-server-setup)
- [OS Setup](#os-setup)
- [Additional Configuration](#additional-configuration)

CCFFFF20051000-3400E2004709B4706821BE0D010C-B75F

## Environment Setup

Set up Message of the Day (MOTD) using ASCII art:

```bash
# Generate ASCII art at the provided TAAG link and add it to your MOTD file
sudo vi /etc/banner
```

```vi
***
You are root act like it
***
```

Configure SSH with no root passwords and a custom port:

```bash
vi /etc/ssh/sshd_config
```

```vi
# Edit your sshd_config file to include:
PermitRootLogin no
Port 8997
```

Disable ipv6
https://support.nordvpn.com/hc/en-us/articles/20164669224337-How-to-disable-IPv6-on-Linux

Here's how to disable IPv6 on Linux if you’re running a Debian-based machine.

Open the terminal window.
Type this command:

sudo nano /etc/sysctl.conf
Add the following at the bottom of the file:

net.ipv6.conf.all.disable_ipv6 = 1
net.ipv6.conf.default.disable_ipv6 = 1
net.ipv6.conf.lo.disable_ipv6 = 1
net.ipv6.conf.tun0.disable_ipv6 = 1
Save and close the file.
Reboot your device.
To re-enable IPv6, remove the above lines from /etc/sysctl.conf and reboot your device.

Before you begin, update your package list and upgrade your system:

```bash
sudo apt update
sudo apt install nala
sudo nala upgrade
```

Install the necessary packages for your terminal and development environment:
Install log2ram and other packages required to edit, configure, and monitor

```bash
echo "deb [signed-by=/usr/share/keyrings/azlux-archive-keyring.gpg] http://packages.azlux.fr/debian/ bookworm main" | sudo tee /etc/apt/sources.list.d/azlux.list
sudo wget -O /usr/share/keyrings/azlux-archive-keyring.gpg  https://azlux.fr/repo.gpg
sudo nala update
sudo nala install zsh exa fzf ripgrep neovim tmux git neofetch nginx nodejs npm postgresql postgresql-contrib tmux thefuck lm-sensors log2ram bat samba atop htop python3-neovim solaar software-properties-common
```

Configure Git - https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent

```
~/.gitconfig
[user]
        name = Thomas Denton
        email = tommydenton@gmail.com
[core]
        editor = vi
[color]
        ui = true
```
Install Bottom
```bash
curl -LO https://github.com/ClementTsang/bottom/releases/download/0.9.6/bottom_0.9.6_arm64.deb
sudo dpkg -i bottom_0.9.6_arm64.deb
```
Run Bottom

```btm --hide_table_gap -f -T```
Change your default shell to Zsh:

```zsh
chsh -s $(which zsh)
```

Install oh-my-zsh

```zsh
sh -c "$(wget https://raw.github.com/ohmyzsh/ohmyzsh/master/tools/install.sh -O -)"
git clone https://github.com/zsh-users/zsh-syntax-highlighting.git ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting
git clone https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions
```

```vi
.zshrc
(git colorize tmux colored-man-pages zsh-autosuggestions zsh-syntax-highlighting thefuck)
change to agnoster
```

Things to Install

https://github.com/dbcli/pgcli
https://github.com/Unitech/pm2
https://github.com/santinic/how2

Configure RTC
https://pimylifeup.com/raspberry-pi-rtc/

```
dtoverlay=i2c-rtc,ds3231
```

Setup up SAMBA
Now that Samba is installed, we need to create a directory for it to share:

```zsh
mkdir /home/<username>/sambashare/
sudo nano /etc/samba/smb.conf
sudo smbpasswd -a pi
```
```vi

[sambashare]
    comment = Samba on Ubuntu
    path = /home/username/sambashare
    read only = no
    browsable = yes
```
Update and Upgrade again

```zsh
sudo nala update
sudo nala upgrade
```

Setup and configure TMUX

```zsh
git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm
```

Install Nerd Fonts for additional glyphs:

```bash
# Replace <nerd-fonts-download-url> and <nerd-fonts-zip-file> with actual values
wget <nerd-fonts-download-url>
unzip <nerd-fonts-zip-file>
cp <nerd-fonts-files> /usr/share/fonts/
cp <nerd-fonts-files> /usr/local/share/fonts/
fc-cache -f -v

Install NPM Packages

```zsh
sudo npm install -g axios body-parser compression darkmode-js debug ejs eslint express-async-errors express fs gg helmet moment morgan multer ntp-client ntp-time ntp pg pm2 save serialport socket.io-client socket.io uuid util connect-flash express-session
sudo npm install axios body-parser compression darkmode-js debug ejs eslint express-async-errors express fs gg helmet moment morgan multer ntp-client ntp-time ntp pg pm2 save serialport socket.io-client socket.io uuid util connect-flash express-session --save
```
```zsh
create the node project
npm init -y
```

To initiate a Node.js project, you'll need to follow a series of steps that involve creating a project directory, initializing the project with a package.json file, and installing any necessary dependencies. Here's a step-by-step guide to get you started:
Create a Project Directory:
First, create a directory for your new application and navigate into it using your terminal or command prompt.
```zsh
mkdir myapp
cd myapp
```

Initialize the Project:
Use the npm init command to create a package.json file for your application. This file will include metadata about your project such as the name, version, description, and dependencies. You can either answer the prompts that appear to customize your package.json or use npm init -y to accept the defaults.
```zsh
npm init -y
```
Install Dependencies:
If your project requires any libraries or frameworks, such as Express for building web applications, you can install them using npm. For example, to install Express and save it as a dependency in your package.json file, run:
```zsh
npm install express --save
```
Create Your Main Application File:
Create a file named index.js (or another entry point if you specified a different file name during initialization) in the root of your project directory. This file will serve as the starting point for your application.
```zsh
echo 'console.log("Hello World!");' > index.js
```
Run Your Application:
You can run your application using Node.js by executing the following command in your terminal:
```zsh
node index.js
```
(Optional) Use nodemon for Development:
For a better development experience, you can install nodemon globally. nodemon will automatically restart your application whenever you make changes to your files.
```zsh
npm install -g nodemon
```
Then, you can start your application with nodemon instead of node:
```zsh
nodemon index.js
```
(Optional) Git Initialization:
It's a good practice to use version control for your project. Initialize a Git repository and create a .gitignore file to exclude node_modules or other non-essential files:
```zsh
git init
echo "node_modules/" > .gitignore
git add .
git commit -m "Initial commit"
```

Run server.js and netapi.js with PM2 then type 'pm2 save' then 'pm2 startup' follow the instructions then reboot


Reference Documents
- https://gist.github.com/dogrocker/1efb8fd9427779c827058f873b94df95
- https://dev.to/andrenbrandao/terminal-setup-with-zsh-tmux-dracula-theme-48lm
- https://medium.com/today-i-learned-chai/setup-node-js-application-with-pm2-and-nginx-72840f44ea73
- https://vexell.medium.com/pm2-module-to-monitoring-node-js-application-with-export-to-prometheus-and-grafana-43d4b958c563
- sudo env PATH=$PATH:/usr/bin /usr/local/lib/node_modules/pm2/bin/pm2 startup systemd -u pi --hp /home/pi
- https://medium.com/today-i-learned-chai/setup-node-js-application-with-pm2-and-nginx-72840f44ea73
- https://github.com/Unitech/pm2

### This README is part of the RFID project documentation. For more information, visit the [project repository](#).

fix PIP installs
https://www.jeffgeerling.com/blog/2023/how-solve-error-externally-managed-environment-when-installing-pip3

install
https://www.pgcli.com/

Setup the database

sudo -i -u postgres
psql
ALTER USER postgres WITH PASSWORD 'new_password';
CREATE DATABASE rfid_system;
exit
psql -U postgres -d rfid_system
CREATE THE TABLES


Environment:
> uname -a
  Linux unsccybercom 6.6.20+rpt-rpi-v8 #1 SMP PREEMPT Debian 1:6.6.20-1+rpt1 (2024-03-07) aarch64 GNU/Linux
> python --version
  Python 3.11.2
> npm -v
  9.2.0
> node -v
  v18.19.0
> sudo nginx -v
  nginx version: nginx/1.22.1
> psql -v
psql (15.6 (Debian 15.6-0+deb12u1))
> npm list
├── axios@1.6.8
├── body-parser@1.20.2
├── compression@1.7.4
├── connect-flash
├── darkmode-js@1.5.7
├── debug@4.3.4
├── ejs@3.1.10
├── eslint@9.1.1
├── express-async-errors@3.1.1
├── express@4.19.2
├── express-session
├── fs@0.0.1-security
├── gg@0.1.3
├── helmet@7.1.0
├── moment@2.30.1
├── morgan@1.10.0
├── multer@1.4.5-lts.1
├── ntp-client@0.5.3
├── ntp-time@2.0.4
├── ntp@0.0.5
├── pg@8.11.5
├── pm2@5.3.1
├── save@2.9.0
├── serialport@12.0.0
├── socket.io-client@4.7.5
├── socket.io@4.7.5
├── util@0.12.5
└── uuid@9.0.1

> tree
├── configfiles
│   ├── nginx.conf
│   └── tree.txt
├── display
│   ├── server.js
│   ├── stamper.js
│   └── views
│       ├── boats.ejs
│       ├── dataentry.ejs
│       ├── deletelink.ejs
│       ├── editboats.ejs
│       ├── editdata.ejs
│       ├── importdata.ejs
│       ├── index.ejs
│       ├── linker.ejs
│       └── rfidlink.ejs
├── index.html
├── ntpapi
│   └── ntpapi.mjs
├── package.json
├── package-lock.json
├── public
│   ├── css
│   │   └── style.css
│   └── js
│       └── darkmode-js.min.js
├── stamp
│   └── stamper.py
└── uploads

> \d+ DEMODATA
                                                                 Table "public.demodata"
   Column   |          Type          | Collation | Nullable |                Default                | Storage  | Compression | Stats target | Description
------------+------------------------+-----------+----------+---------------------------------------+----------+-------------+--------------+-------------
 uid        | integer                |           | not null | nextval('demodata_uid_seq'::regclass) | plain    |             |              |
 fname      | character varying(255) |           |          |                                       | extended |             |              |
 lname      | character varying(255) |           |          |                                       | extended |             |              |
 gender     | character varying(255) |           |          |                                       | extended |             |              |
 age        | character varying(255) |           |          |                                       | extended |             |              |
 council    | character varying(255) |           |          |                                       | extended |             |              |
 district   | character varying(255) |           |          |                                       | extended |             |              |
 unittype   | character varying(255) |           |          |                                       | extended |             |              |
 unitnumber | integer                |           |          |                                       | plain    |             |              |
 race       | character varying(255) |           |          |                                       | extended |             |              |
 boat       | character varying(255) |           |          |                                       | extended |             |              |
 bibnumber  | integer                |           |          |                                       | plain    |             |              |
Indexes:
    "demodata_pkey" PRIMARY KEY, btree (uid)
    "demodata_bibnumber_key" UNIQUE CONSTRAINT, btree (bibnumber)
Access method: heap

> \d+ LINKER
    Column    |          Type          | Collation | Nullable |               Default               | Storage  | Compression | Stats target | Description
--------------+------------------------+-----------+----------+-------------------------------------+----------+-------------+--------------+-------------
 uid          | integer                |           | not null | nextval('linker_uid_seq'::regclass) | plain    |             |              |
 bibnumber    | integer                |           |          |                                     | plain    |             |              |
 rfidtag      | character varying(255) |           |          |                                     | extended |             |              |
 tag_type     | character varying(255) |           |          |                                     | extended |             |              |
 tag_id       | character varying(255) |           |          |                                     | extended |             |              |
 tag_position | character varying(255) |           |          |                                     | extended |             |              |
Indexes:
    "linker_pkey" PRIMARY KEY, btree (uid)
    "linker_bibnumber_key" UNIQUE CONSTRAINT, btree (bibnumber)
    "linker_rfidtag_key" UNIQUE CONSTRAINT, btree (rfidtag)
Access method: heap

> \d+ BOATS
                                                             Table "public.boats"
   Column   |  Type   | Collation | Nullable |                  Default                  | Storage | Compression | Stats target | Description
------------+---------+-----------+----------+-------------------------------------------+---------+-------------+--------------+-------------
 uid        | integer |           | not null | nextval('boats_uid_seq'::regclass)        | plain   |             |              |
 bibnumber1 | integer |           |          |                                           | plain   |             |              |
 bibnumber2 | integer |           |          |                                           | plain   |             |              |
 boatnumber | integer |           | not null | nextval('boats_boatnumber_seq'::regclass) | plain   |             |              |
Indexes:
    "boats_pkey" PRIMARY KEY, btree (uid)
    "unique_bibnumber_pair" UNIQUE CONSTRAINT, btree (bibnumber1, bibnumber2)
Access method: heap

 \d+ TIMERESULTS
                                                                  Table "public.timeresults"
    Column    |          Type          | Collation | Nullable |                 Default                 | Storage  | Compression | Stats target | Description
--------------+------------------------+-----------+----------+-----------------------------------------+----------+-------------+--------------+-------------
 id           | integer                |           | not null | nextval('timeresults_id_seq'::regclass) | plain    |             |              |
 tag_type     | character varying(255) |           |          |                                         | extended |             |              |
 tag_id       | character varying(255) |           |          |                                         | extended |             |              |
 tag_position | character varying(255) |           |          |                                         | extended |             |              |
 timestamp    | double precision       |           |          |                                         | plain    |             |              |
 timestamp_h  | character varying(255) |           |          |                                         | extended |             |              |
Indexes:
    "timeresults_pkey" PRIMARY KEY, btree (id)
Access method: heap


Setup the database on the timers:

Certainly! Here are the steps to set up the PostgreSQL database rfid_system and the table timeresults on your Debian system.

Step-by-Step Instructions
1. Switch to the PostgreSQL User:
  sudo -i -u postgres
2. Open the PostgreSQL Interactive Terminal:
  psql
3. Create the Database:
  CREATE DATABASE rfid_system;
4. Connect to the New Database:
  \c rfid_system
5. Create the timeresults Table:
  CREATE TABLE timeresults (
      id SERIAL PRIMARY KEY,
      tag_type VARCHAR(255),
      tag_id VARCHAR(255),
      tag_position VARCHAR(255),
      timestamp DOUBLE PRECISION,
      timestamp_h VARCHAR(255)
  );
6. Verify the Table:
  \d+ timeresults
7. PASSWORD THE USER
  To log in without a password:
    sudo -u postgres psql rfid_system
  To reset the password if you have forgotten:
    ALTER USER postgres WITH PASSWORD 'r0ckkrush3r';
8. Check for data
  select * from timeresults;


Added Scripts folder that has the export and deploy script it in.
you will have to update the pg_hba.conf file to allow for exports

the line local/all/postgres/peer changes to local/all/postgres/md5

https://stackoverflow.com/questions/18664074/getting-error-peer-authentication-failed-for-user-postgres-when-trying-to-ge
