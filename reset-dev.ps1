#!/bin/bash
# reset-dev.sh
try {
 
git checkout dev
git fetch origin
git reset --hard origin/main
git push --force-with-lease origin dev  
}
catch {
 exit 1   
}