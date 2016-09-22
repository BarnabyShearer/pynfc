test_publish:
	python3 setup.py sdist bdist_wheel upload --sign -r https://testpypi.python.org/pypi

publish:
	python3 setup.py sdist bdist_wheel upload --sign
