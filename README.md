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

Before you begin, update your package list and upgrade your system:

```bash
sudo apt update
sudo apt upgrade
```

Install the necessary packages for your terminal and development environment:

```bash
sudo apt update
sudo apt install nala

sudo nala install zsh exa fzf ripgrep neovim tmux git zsh-syntax-highlighting nginx nodejs npm postgresql postgresql-contrib tmux zsh-autosuggestions thefuck lm-sensors

echo "deb [signed-by=/usr/share/keyrings/azlux-archive-keyring.gpg] http://packages.azlux.fr/debian/ bookworm main" | sudo tee /etc/apt/sources.list.d/azlux.list
sudo wget -O /usr/share/keyrings/azlux-archive-keyring.gpg  https://azlux.fr/repo.gpg
sudo apt update
sudo apt install log2ram

```

Change your default shell to Zsh:

```bash
chsh -s $(which zsh)
```

Install Oh My Zsh for managing your Zsh configuration:

```bash
sh -c "$(wget https://raw.github.com/ohmyzsh/ohmyzsh/master/tools/install.sh -O -)"

then 

https://gist.github.com/dogrocker/1efb8fd9427779c827058f873b94df95

then

https://dev.to/andrenbrandao/terminal-setup-with-zsh-tmux-dracula-theme-48lm

then

curl -LO https://github.com/ClementTsang/bottom/releases/download/0.9.6/bottom_0.9.6_amd64.deb
sudo dpkg -i bottom_0.9.6_amd64.deb

then

https://github.com/ClementTsang/bottom?tab=readme-ov-file#usage

then

git clone https://github.com/wfxr/forgit.git ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/forgit

then

plugins=(git tmux colored-man-pages zsh-autosuggestions zsh-syntax-highlighting )

and

https://medium.com/today-i-learned-chai/setup-node-js-application-with-pm2-and-nginx-72840f44ea73

and

https://vexell.medium.com/pm2-module-to-monitoring-node-js-application-with-export-to-prometheus-and-grafana-43d4b958c563
```

Install Nerd Fonts for additional glyphs:

```bash
# Replace <nerd-fonts-download-url> and <nerd-fonts-zip-file> with actual values
wget <nerd-fonts-download-url>
unzip <nerd-fonts-zip-file>
cp <nerd-fonts-files> /usr/share/fonts/
cp <nerd-fonts-files> /usr/local/share/fonts/
fc-cache -f -v
```

sudo npm install gg
npm install body-parser

apt install postgres postgres-contrib

Configure your shell prompt with Starship:

```bash
echo 'eval "$(starship init zsh)"' >> ~/.zshrc
```

Set up Message of the Day (MOTD) using ASCII art:

```bash
# Generate ASCII art at the provided TAAG link and add it to your MOTD file
```

Configure SSH with no root passwords and a custom port:

```bash
# Edit your sshd_config file to include:
PermitRootLogin no
Port 8997
```

Install additional utilities:

```bash
sudo apt install log2ram nala
```

## Webserver Setup

Install and configure Nginx:

```bash
sudo apt install nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

## API Server Setup

Install Node.js and npm, and the necessary Node packages:
https://medium.com/today-i-learned-chai/setup-node-js-application-with-pm2-and-nginx-72840f44ea73

```bash
sudo apt install nodejs npm
npm install ntp express ntp-client express ejs axios ntp-time pm2
sudo env PATH=$PATH:/usr/bin /usr/local/lib/node_modules/pm2/bin/pm2 startup systemd -u pi --hp /home/pi

```

## OS Setup

Your Raspberry Pi with Bullseye OS should have the following standard installations:

```bash
sudo apt install nginx nodejs postgresql npm
```

## Additional Configuration

Remember to configure your PostgreSQL database and any other OS-level configurations specific to your RFID project.

For detailed instructions on setting up Python and the timer, as well as additional configurations, refer to the respective sections in this guide.

---

This README is part of the RFID project documentation. For more information, visit the [project repository](#).
```

You can copy and paste this markdown into a `README.md` file in your GitHub repository. Make sure to replace placeholder text such as `<nerd-fonts-download-url>` and `<nerd-fonts-zip-file>` with the actual URLs and file names before publishing.
