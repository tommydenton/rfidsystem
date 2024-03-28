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
sudo nala install zsh exa fzf ripgrep neovim tmux git neofetch nginx nodejs npm postgresql postgresql-contrib tmux thefuck lm-sensors log2ram
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
sudo npm install -g pm2 gg ntp express ntp-client express ejs axios ntp-time body-parser
```
```zsh
create the node project
npm init -y
```

To initiate a Node.js project, you'll need to follow a series of steps that involve creating a project directory, initializing the project with a package.json file, and installing any necessary dependencies. Here's a step-by-step guide to get you started:
Create a Project Directory:
First, create a directory for your new application and navigate into it using your terminal or command prompt.
bash
mkdir myapp
cd myapp

Initialize the Project:
Use the npm init command to create a package.json file for your application. This file will include metadata about your project such as the name, version, description, and dependencies. You can either answer the prompts that appear to customize your package.json or use npm init -y to accept the defaults.
bash
npm init -y

Install Dependencies:
If your project requires any libraries or frameworks, such as Express for building web applications, you can install them using npm. For example, to install Express and save it as a dependency in your package.json file, run:
bash
npm install express --save

Create Your Main Application File:
Create a file named index.js (or another entry point if you specified a different file name during initialization) in the root of your project directory. This file will serve as the starting point for your application.
bash
echo 'console.log("Hello World!");' > index.js

Run Your Application:
You can run your application using Node.js by executing the following command in your terminal:
bash
node index.js

(Optional) Use nodemon for Development:
For a better development experience, you can install nodemon globally. nodemon will automatically restart your application whenever you make changes to your files.
bash
npm install -g nodemon

Then, you can start your application with nodemon instead of node:
bash
nodemon index.js

(Optional) Git Initialization:
It's a good practice to use version control for your project. Initialize a Git repository and create a .gitignore file to exclude node_modules or other non-essential files:
bash
git init
echo "node_modules/" > .gitignore
git add .
git commit -m "Initial commit"

This guide provides a basic setup for a Node.js project. Depending on your project's requirements, you may need to install additional packages or configure other tools

Reference Documents
- https://gist.github.com/dogrocker/1efb8fd9427779c827058f873b94df95
- https://dev.to/andrenbrandao/terminal-setup-with-zsh-tmux-dracula-theme-48lm
- https://medium.com/today-i-learned-chai/setup-node-js-application-with-pm2-and-nginx-72840f44ea73
- https://vexell.medium.com/pm2-module-to-monitoring-node-js-application-with-export-to-prometheus-and-grafana-43d4b958c563
- sudo env PATH=$PATH:/usr/bin /usr/local/lib/node_modules/pm2/bin/pm2 startup systemd -u pi --hp /home/pi
- https://medium.com/today-i-learned-chai/setup-node-js-application-with-pm2-and-nginx-72840f44ea73

### This README is part of the RFID project documentation. For more information, visit the [project repository](#).
