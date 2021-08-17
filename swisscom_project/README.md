## SWISSCOM Test Project

This project includes solving the problem of creating and 
deleting records for remote services using the API methods 
of these services, such as POST (create), DELETE (delete) 
and GET (check) records. I solve this problem in two ways: 
classic and asynchronous, here both options 
(folders classic_variant and async_variant). 
When solving this problem, the logic of both options is as follows:


* Сheck the availability of the required record on third-party 
API(GET method).
* Save the status of the presence or absence of records on hosts.
* If at the previous stage one or more hosts are unavailable, we 
reject the request to create or delete.
* With the received info about the state of the data 
on the hosts, we try to create / delete records.
* If all is well, mission accomplished!
* If not, we delete / re-create the records that we tried 
to create / delete, returning 
back to the original state before the operation.

## Install

### install requirements

```bash
pip3 install -r requirements.txt
```

### run tests

```bash
pytest
pytest -k test_ok
pytest -k test_async_fail_host_responding
...
```

## Usage

### run connector

```bash
Connector(hosts=HOSTS)
connector.create(group_id="4a2850db-b328-4c10-9ef0-0dc560068291")
```

## Errors

* `HostRespondingError` - one or more hosts are unavailable
* `RollBackOperationError` - an error occurred during the create / delete operation - roll back