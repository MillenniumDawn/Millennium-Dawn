@ECHO OFF


ECHO | set /p=Current Branch: 
git symbolic-ref --short HEAD
ECHO Updating branch cause i can't do it my self...
cd ..
ECHO Updating local reposetory...
git fetch
ECHO Rebasing local branch...
git rebase --abort 
git rebase master 
cd tools
ECHO Compleet.