test:
	@pylint smeltme --disable=line-too-long
	@flake8 smeltme --ignore=E501
