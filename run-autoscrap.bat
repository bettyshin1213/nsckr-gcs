@echo off

cd C:\git\nsckr-autoscrap

git checkout main
git status
git pull
git status

python -m venv auto
call auto\Scripts\activate.bat

pip install -r requirements.txt

python src\autoscrap.py

pause