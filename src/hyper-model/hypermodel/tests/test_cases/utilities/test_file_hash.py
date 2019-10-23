from hypermodel.utilities.file_hash import file_md5

def test_file_md5():
    expected_return_value="8348f98f61cf58d6e7921c173bd0286d"
    actual_return_value=file_md5("C:\\Amit\\hypermodel\\hyper-model\\src\\hyper-model\\hypermodel\\tests\\test_data\\dummy_file.txt")
    assert expected_return_value==actual_return_value
