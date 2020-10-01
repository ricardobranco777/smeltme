test:
	@pylint smeltme --disable=too-many-locals,line-too-long
	@flake8 smeltme --ignore=E501
