Please follow the below instructions for writting unit test for code

* The Testing is done using the Pytest frame
* To run a test for a single file use the following code:
\`\`\`
pytest --cov=app --cov-report xml:cov.xml Tests/Test_app.py 
\`\`\`
* The code coverage for each file should be above 80%
* Run unit test and code coverage for all files in the Tests folder
\`\`\`
 pytest --cov=app --cov=appGet --cov=appSet --cov-report xml:cov.xml -v Tests
 pytest --cov=app --cov=appGet --cov=appSet --cov-report html:cov.html -v Tests
\`\`\`







