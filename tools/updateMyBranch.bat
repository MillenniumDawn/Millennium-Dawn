@ECHO OFF

ECHO Updating my branch cause i can't do it my self...
cd ..
ECHO Updating local reposetory...
git fetch
ECHO Rebasing local branch...
git rebase master
cd tools
ECHO Compleet.