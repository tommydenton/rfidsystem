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
sudo nala install zsh exa fzf ripgrep neovim tmux git neofetch nginx nodejs npm postgresql postgresql-contrib tmux thefuck lm-sensors log2ram samba atop htop python3-neovim
```

Install Bottom
```bash
curl -LO https://github.com/ClementTsang/bottom/releases/download/0.9.6/bottom_0.9.6_arm64.deb
sudo dpkg -i bottom_0.9.6_arm64.deb
```

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
sudo npm install -g multer uuid@latest express axios moment serialport pm2 gg pg ntp ntp-client ejs ntp-time body-parser socket.io-client socket.io  darkmode-js
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
timer@ /var/www/html/timer
├── axios@1.6.8
├── body-parser@1.20.2
├── darkmode-js@1.5.7
├── debug@4.3.4
├── ejs@3.1.9
├── express@4.19.2
├── fs@0.0.1-security
├── gg@0.1.3
├── moment@2.30.1
├── multer@1.4.5-lts.1
├── ntp-client@0.5.3
├── ntp-time@2.0.4
├── ntp@0.0.5
├── pg@8.11.5
├── pm2@5.3.1
├── serialport@12.0.0
├── socket.io-client@4.7.5
├── socket.io@4.7.5
└── uuid@9.0.1

> tree
├├── configfiles
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
│       ├── index.ejs
│       └── linker.ejs
├── index.html
├── ntpapi
│   └── ntpapi.mjs
├── public
│   ├── css
│   │   └── style.css
│   └── js
│       └── darkmode-js.min.js
├── stamp
    └── stamper.py


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
                                                                 Table "public.linker"
  Column   |          Type          | Collation | Nullable |               Default               | Storage  | Compression | Stats target | Description
-----------+------------------------+-----------+----------+-------------------------------------+----------+-------------+--------------+-------------
 uid       | integer                |           | not null | nextval('linker_uid_seq'::regclass) | plain    |             |              |
 bibnumber | integer                |           |          |                                     | plain    |             |              |
 rfidtag   | character varying(255) |           |          |                                     | extended |             |              |
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