Please follow the below instructions for writting unit test for code

* The Testing is done using the Pytest frame
* The code coverage for each file should be above 80%
* Run unit test and code coverage for all files in the Tests folder


```bash
pytest --cov=. --cov-config=.coveragerc --cov-report html:cov.html -v Tests
```

Another test commands that you can run 
```bash
pytest --cov=. --cov-report term -v Tests
pytest --cov=. --cov-report xml:cov.xml -v Tests -W ignore
pytest --cov=. --cov-report html:cov.html -v Tests -W ignore
pytest --cov=. --cov-report html:cov.html -v Tests -W ignore --cov-exclude=Tests/
pytest --cov=. --cov-config=.coveragerc --cov-report html:cov.html -v Tests
```
