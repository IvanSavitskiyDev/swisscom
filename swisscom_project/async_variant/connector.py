import logging
from typing import Dict, List, Optional

import grequests
from swisscom_project.common.dataclasses import HttpMethod, RequestState
from swisscom_project.common.exceptions import (
    HostRespondingError,
    RollBackOperationError,
)

logging.basicConfig(level=logging.INFO)


class AsyncConnector:
    def __init__(self, hosts: List[str]) -> None:
        self.hosts = hosts

    def create(self, group_id: str) -> None:
        """
        The method allows you to create records on all hosts
        from the list 'self.hosts' at the same time
        """
        logging.info(f"Start creating records on hosts: {self.hosts}")
        check_existing: Dict[str, RequestState] = self._check_existing(
            self.hosts, group_id
        )

        hosts_without_group_id: List[str] = [
            host
            for host, status in check_existing.items()
            if status == RequestState.NOT_FOUND
        ]
        logging.info(f"Hosts without current group_id record: {hosts_without_group_id}")

        batch_creation_hosts: Dict[str, RequestState] = self._batch_api_request(
            HttpMethod.POST, hosts_without_group_id, group_id
        )
        logging.info(f"Status after creating records: {batch_creation_hosts}")

        hosts_creation_failed: List[str] = [
            host
            for host, status in batch_creation_hosts.items()
            if status == RequestState.FAIL
        ]
        if hosts_creation_failed:
            logging.warning(
                f"The operation will be revert, these hosts are not responding: {hosts_creation_failed}"
            )
            hosts_creation_success: List[str] = [
                host
                for host, status in batch_creation_hosts.items()
                if status == RequestState.SUCCESS
            ]

            batch_removing_hosts: Dict[str, RequestState] = self._batch_api_request(
                HttpMethod.DELETE, hosts_creation_success, group_id
            )
            logging.info(f"Status after deleting records: {batch_removing_hosts}")
            logging.info("Operation rolled back successfully")
            raise RollBackOperationError("Operation rolled back")

        logging.info("Successfully create records for all nodes")

    def delete(self, group_id: str) -> None:
        """
        The method allows you to delete records on all hosts
        from the list 'self.hosts' at the same time
        """
        logging.info(f"Start removing records on hosts: {self.hosts}")
        check_existing: Dict[str, RequestState] = self._check_existing(
            self.hosts, group_id
        )

        hosts_with_group_id: List[str] = [
            host
            for host, status in check_existing.items()
            if status == RequestState.SUCCESS
        ]
        logging.info(f"Hosts with current group_id record: {hosts_with_group_id}")

        batch_removing_hosts: Dict[str, RequestState] = self._batch_api_request(
            HttpMethod.DELETE, hosts_with_group_id, group_id
        )
        logging.info(f"Status after removing records: {batch_removing_hosts}")

        hosts_removing_failed: List[str] = [
            host
            for host, status in batch_removing_hosts.items()
            if status == RequestState.FAIL
        ]
        if hosts_removing_failed:
            logging.warning(
                f"The operation will be revert, these hosts are not responding: {hosts_removing_failed}"
            )
            hosts_removing_success: List[str] = [
                host
                for host, status in batch_removing_hosts.items()
                if status == RequestState.SUCCESS
            ]

            batch_recovery_hosts: Dict[str, RequestState] = self._batch_api_request(
                HttpMethod.POST, hosts_removing_success, group_id
            )
            logging.info(f"Status after recovery records: {batch_recovery_hosts}")
            logging.info("Operation rolled back successfully")
            raise RollBackOperationError("Operation rolled back")

        logging.info("Successfully delete records for all nodes")

    @staticmethod
    def _state_machine(
        status_code: int, http_method: Optional[HttpMethod] = None
    ) -> RequestState:
        """
        Simple state machine for our dataclasses
        """
        if status_code == 404:
            if http_method is None:
                current_request = RequestState.NOT_FOUND
            else:
                current_request = RequestState.FAIL

        elif status_code == 200:
            current_request = RequestState.SUCCESS

        else:
            current_request = RequestState.FAIL

        return current_request

    def _check_existing(
        self, local_hosts: List[str], group_id: str
    ) -> Dict[str, RequestState]:
        """
        the method checks for the presence of records on the hosts
        before creating / deleting and for the availability of hosts
        """
        payload: Dict[str, str] = {"group_id": group_id}
        full_urls = [f"http://{host}/v1/group/" for host in local_hosts]
        rs = (grequests.get(url, params=payload) for url in full_urls)
        result: Dict[str, RequestState] = {
            local_hosts[index]: self._state_machine(value.status_code)
            for index, value in enumerate(grequests.map(rs))
        }

        hosts_check_failed: List[str] = [
            host for host, status in result.items() if status == RequestState.FAIL
        ]
        if hosts_check_failed:
            logging.error(
                f"Operation rejected, these hosts are not responding: {hosts_check_failed}"
            )
            raise HostRespondingError("Some hosts are not responding")

        return result

    def _batch_api_request(
        self, http_method: HttpMethod, local_hosts: List[str], group_id: str
    ) -> Dict[str, RequestState]:
        """
        batch request for create/delete records,
        used by switching by the passed http_method var
        """
        payload: Dict[str, str] = {"group_id": group_id}
        full_urls = [f"http://{host}/v1/group/" for host in local_hosts]
        if http_method == HttpMethod.POST:
            rs = (grequests.post(url, params=payload) for url in full_urls)
        else:
            rs = (grequests.delete(url, params=payload) for url in full_urls)

        return {
            local_hosts[index]: self._state_machine(value.status_code, http_method)
            for index, value in enumerate(grequests.map(rs))
        }
