import pytest
import requests_mock
from swisscom_project.classic_variant.connector import Connector
from swisscom_project.classic_variant.exceptions import (
    HostRespondingError, RollBackOperationError)

HOSTS = [
    "node01.app.internal.com",
    "node02.app.internal.com",
    "node03.app.internal.com",
    "node04.app.internal.com",
]


@pytest.fixture(scope="module")
def connector():
    return Connector(hosts=HOSTS)


@pytest.mark.parametrize(
    "status_code_list",
    (
        [404, 404, 404, 404],  # Got "NOT_FOUND" for all hosts
        [404, 404, 404, 200],  # The entry exists for one last host
    ),
)
@pytest.mark.parametrize("create_or_delete", (True, False))
def test_ok(connector, status_code_list, create_or_delete):
    # We check the work both in the absence
    # of records on all hosts and in the presence
    with requests_mock.Mocker(real_http=True) as m:
        for index, host in enumerate(HOSTS):
            m.get(f"http://{host}/v1/group/", status_code=status_code_list[index])

        if create_or_delete:
            response = connector.create(group_id="1")
        else:
            response = connector.delete(group_id="1")
        assert response is None


@pytest.mark.parametrize("create_or_delete", (True, False))
def test_fail_host_responding(connector, create_or_delete):
    # If one of the hosts does not respond
    # during the verification phase, an exception is thrown

    with requests_mock.Mocker(real_http=True) as m:
        m.get(f"http://node03.app.internal.com/v1/group/", status_code=500)

        with pytest.raises(HostRespondingError):
            if create_or_delete:
                connector.create(group_id="1")
            else:
                connector.delete(group_id="1")


@pytest.mark.parametrize("create_or_delete", (True, False))
def test_fail_roll_back(connector, create_or_delete):
    # If one of the hosts does not respond
    # during the verification phase, an exception is thrown

    with requests_mock.Mocker(real_http=True) as m:
        if create_or_delete:
            m.get(f"http://node01.app.internal.com/v1/group/", status_code=404)
            m.get(f"http://node02.app.internal.com/v1/group/", status_code=404)
            m.get(f"http://node03.app.internal.com/v1/group/", status_code=404)
            m.post(f"http://node02.app.internal.com/v1/group/", status_code=404)
        else:
            m.get(f"http://node01.app.internal.com/v1/group/", status_code=200)
            m.get(f"http://node02.app.internal.com/v1/group/", status_code=200)
            m.get(f"http://node03.app.internal.com/v1/group/", status_code=200)
            m.delete(f"http://node02.app.internal.com/v1/group/", status_code=404)

        with pytest.raises(RollBackOperationError):
            if create_or_delete:
                connector.create(group_id="1")
            else:
                connector.delete(group_id="1")
