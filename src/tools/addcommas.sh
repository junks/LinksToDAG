#!/bin/sh

#taken from: http://stackoverflow.com/questions/14668094/add-commas-to-numeric-strings-in-unix

sed -e ': L
s/\([0-9]\{1,19\}\)\([0-9]\{3\}\)/\1,\2/
t L'