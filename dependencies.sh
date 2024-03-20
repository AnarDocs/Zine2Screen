#!/bin/bash

# Install dependencies

# Function to install packages on Debian/Ubuntu
install_debian() {
    sudo apt update
    sudo apt install -y poppler-utils imagemagick ghostscript
}

# Function to install packages on Redhat/Fedora
install_redhat() {
    sudo yum install -y poppler-utils ImageMagick ghostscript
}

# Function to install packages on MacOS
install_macos() {
    brew install poppler imagemagick ghostscript
}

# Detect the operating system
if [[ "$(uname)" == "Linux" ]]; then
    if [ -f "/etc/debian_version" ]; then
        echo "Detected Debian/Ubuntu"
        install_debian
    elif [ -f "/etc/redhat-release" ]; then
        echo "Detected Redhat/Fedora"
        install_redhat
    else
        echo "Unknown Linux distribution. Please install required packages manually."
    fi
elif [[ "$(uname)" == "Darwin" ]]; then
    echo "Detected MacOS"
    install_macos
else
    echo "Unsupported operating system."
fi
