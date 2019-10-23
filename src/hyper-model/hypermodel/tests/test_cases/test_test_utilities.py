from hypermodel.tests.utilities.configurations import TestConfig

def test_test_configuration_positive():
    test_config=TestConfig()
    assert test_config.get("TESTING_THE_TEST_FILE","TEST_ENTRY")=="1"

def test_test_configuration_nagative():
    test_config=TestConfig()
    assert test_config.get("NOT THERE","NOT THERE")==None
