# commit.ps1
param([string]$msg)

git checkout dev
git add .
git commit -m "$msg"
git push origin dev
