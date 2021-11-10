format:
	isort .
	black .

test:
	tox -e py39

test_all:
	tox
