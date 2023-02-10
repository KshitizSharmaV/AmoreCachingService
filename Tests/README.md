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

VSCode: Erorr while running Tests in.

There are certain times your VSCode will stop detecting tests and will display an error message "". There are certain things you can do debug the issue. 

* If you are trying to run all of your unit tests in VS Code, but there is no command available to do so, it is likely that the appropriate extension for your test framework is not installed. Here are the steps to run all unit tests in VS Code:
* Install the appropriate extension for your test framework. For example, if you are using Pytest, you can install the "Python Test Explorer" extension.
Open the Command Palette by pressing Ctrl+Shift+P on Windows or Cmd+Shift+P on macOS.
* Type "Python: Discover Tests" and press enter. This will discover all the tests in your project and should show the tests in the Test Explorer window.
* Type "Test: Run All Tests" and press enter. This will discover all the tests in your project and should show the tests in the Test Explorer window.
* To run all of your unit tests, click the "Run All" button in the Test Explorer window, or you can use the shortcut Ctrl+Shift+T on Windows or Cmd+Shift+T on macOS.
* If you have multiple test frameworks installed, you'll need to make sure the right test framework is selected in the Test Explorer window.
* If you're still not able to run the tests after trying these steps, it's possible that there may be an issue with your test configuration. Make sure that your test files are named correctly, located in the correct directory, and that your launch.json file is configured correctly for your test framework.
* Run following command in your amorecachingservice folder: 
```bash
pytest --collect-only
```
* Some users also solved the problem by place "__init__.py" in the "Tests" folder and the root folder as well
* You can also check the ".vscode>settings.json" folder in your VSCode editort. The file should look something like this 
* Run following command in your amorecachingservice folder: 
```bash
pytest --collect-only
```
* Some users also solved the problem by place "__init__.py" in the "Tests" folder and the root folder as well
* You can also check the ".vscode>settings.json" folder in your VSCode editort. The file should look something like this 
```bash
{
    "python.testing.pytestArgs": [
        "Tests"
    ],
    "python.testing.unittestEnabled": false,
    "python.testing.pytestEnabled": true
}
```
* Sometimes your tests could have declaration/syntax issues which will cause the test crawler to fail and the tests could be skipped as well
* FYI - PyTests not recognizing tests: When you write an incorrect decorator syntax, the Pytest Stops recognizing all the tests. Because Pytest uses the decorator '@pytest.mark.asyncio' or 'test_' to recognize pytests. So with an invalid syntax you are breaking the Pytest's ability to crawl all the tests and it shows error like "Pytests not found"
* Also note non-async function don't have decorator. Non-Async functions don't have to be decorated with '@pytest.mark.sync'. Non async starting with 'test_' are automatically recognized by Pytest