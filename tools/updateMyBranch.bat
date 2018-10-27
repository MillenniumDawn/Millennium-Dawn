@ECHO OFF

ECHO Updating branch cause i apperently can't do it my self...


git fetch -v --progress "origin"

git pull --progress -v --no-rebase "origin" master
