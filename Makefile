test:
	@pylint smeltme --disable=line-too-long,too-many-locals
	@flake8 smeltme --ignore=E501
