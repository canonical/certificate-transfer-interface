# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

import json

import pytest
from ops import testing

from tests.unit.charms.certificate_transfer_interface.v1.dummy_requirer_charm.src.charm import (
    DummyCertificateTransferRequirerCharm,
)

BASE_LIB_DIR = "lib.charms.certificate_transfer_interface.v1.certificate_transfer"
BASE_CHARM_DIR = "tests.unit.charms.certificate_transfer_interface.v1.dummy_requirer_charm.src.charm.DummyCertificateTransferRequirerCharm"  # noqa: E501


class TestCertificateTransferRequiresV1:
    @pytest.fixture(scope="function", autouse=True)
    def setUp(self):
        self.unit_name = "certificate-transfer-interface-requirer/0"
        self.harness = testing.Harness(DummyCertificateTransferRequirerCharm)
        self.harness.begin()
        yield
        self.harness.cleanup()

    def create_certificate_transfer_relation(self) -> int:
        relation_name = "certificates"
        remote_app_name = "certificate-transfer-provider"
        relation_id = self.harness.add_relation(
            relation_name=relation_name,
            remote_app=remote_app_name,
        )
        return relation_id

    def test_given_certificates_in_relation_data_when_relation_changed_then_certificate_available_event_is_emitted(  # noqa: E501
        self, caplog: pytest.LogCaptureFixture
    ):
        remote_app_name = "certificate-transfer-provider"
        relation_id = self.create_certificate_transfer_relation()
        certificates = {"cert1"}
        databag_value = json.dumps(list(certificates))
        key_values = {
            "certificates": databag_value,
        }
        self.harness.update_relation_data(
            relation_id=relation_id, app_or_unit=remote_app_name, key_values=key_values
        )
        logs = [(record.levelname, record.module, record.message) for record in caplog.records]
        assert (
            "INFO",
            "charm",
            str(certificates),
        ) in logs

    def test_given_certificates_in_relation_data_when_relation_removed_then_certificates_removed_event_is_emitted(  # noqa: E501
        self, caplog: pytest.LogCaptureFixture
    ):
        remote_app_name = "certificate-transfer-provider"
        relation_id = self.create_certificate_transfer_relation()
        certificates = {"cert1"}
        databag_value = json.dumps(list(certificates))
        key_values = {
            "certificates": databag_value,
        }
        self.harness.update_relation_data(
            relation_id=relation_id, app_or_unit=remote_app_name, key_values=key_values
        )
        self.harness.remove_relation(relation_id)
        logs = [(record.levelname, record.module, record.message) for record in caplog.records]
        expected_log = (
            "INFO",
            "charm",
            str(relation_id),
        )
        assert (expected_log == logs[-1]) and (expected_log == logs[-2])

    def test_given_none_of_the_expected_keys_in_relation_data_when_relation_changed_then_warning_log_is_emitted(  # noqa: E501
        self, caplog
    ):
        remote_app_name = "certificate-transfer-provider"
        relation_id = self.create_certificate_transfer_relation()
        certificates = {"cert1"}
        databag_value = json.dumps(list(certificates))
        key_values = {
            "certificatees": databag_value,
        }
        self.harness.update_relation_data(
            relation_id=relation_id, app_or_unit=remote_app_name, key_values=key_values
        )
        self.harness.remove_relation(relation_id)
        logs = [(record.levelname, record.module, record.message) for record in caplog.records]
        assert ("INFO", "charm", "set()") in logs

    def test_given_no_relation_available_when_relation_changed_then_lempty_set_returned(self):
        certificates = self.harness.charm.certificate_transfer.get_all_certificates()
        assert certificates == set()
