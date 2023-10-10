#!/bin/bash

install_debian_deps() {
    dep_path=$1
    apt update -y
    apt upgrade -y
    while read library; do
        apt install -y $library
    done <$dep_path
}

install_centos_deps() {
    dep_path=$1
    microdnf update -y
    while read library; do
        echo "Installing $library"
        microdnf install -y $library
    done <$dep_path
}

get_distro_type() {
    cat /etc/os-release | grep ID_LIKE | cut -b 9-
}

path=$1
distro_type=$(get_distro_type)
if [ "$distro_type" == '"rhel centos fedora"' ]; then
echo "Installing rhel-like dependencies"
    install_centos_deps $path
elif [ "$distro_type" == '"debian"']; then
    install_debian_deps $path
fi
