source .venv/bin/activate

python3 -m pip install --upgrade pip
python3 -m pip install --upgrade build twine

rm -rf dist build *.egg-info

python3 -m build
python3 -m twine check dist/*
python3 -m twine upload dist/*