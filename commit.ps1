# commit.ps1
param([string]$msg)

git add .
git commit -m "$msg"
git push
