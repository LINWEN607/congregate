#!/bin/bash

ls -al $GITLAB_HOME/
rm -rf $GITLAB_HOME/config/*
rm -rf $GITLAB_HOME/logs/*
rm -rf $GITLAB_HOME/data/*

ls -al $LDAP_HOME/
rm -rf $LDAP_HOME/data
rm -rf $LDAP_HOME/slapd.d
mkdir -p $LDAP_HOME/data
