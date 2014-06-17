import os
import pytest


@pytest.fixture(scope='module')
def file_fixture(request):
    dirpath, filename = os.path.split(request.module.__file__)
    test_module, _ = os.path.splitext(filename)
    fixture_path = os.path.join(dirpath, 'fixtures', test_module)

    def file_fixture(fn, open=open):
        return open(os.path.join(fixture_path, fn))

    return file_fixture
