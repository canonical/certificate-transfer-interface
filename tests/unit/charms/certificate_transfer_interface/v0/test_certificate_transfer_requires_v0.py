# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

import json
import unittest
from unittest.mock import MagicMock, patch

from ops import testing

from tests.unit.charms.certificate_transfer_interface.v0.dummy_requirer_charm.src.charm import (
    DummyCertificateTransferRequirerCharm,
)

BASE_LIB_DIR = "lib.charms.certificate_transfer_interface.v0.certificate_transfer"
BASE_CHARM_DIR = "tests.unit.charms.certificate_transfer_interface.v0.dummy_requirer_charm.src.charm.DummyCertificateTransferRequirerCharm"


class TestCertificateTransferRequiresV0(unittest.TestCase):
    def setUp(self):
        self.unit_name = "certificate-transfer-interface-requirer/0"
        self.harness = testing.Harness(DummyCertificateTransferRequirerCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()

    def create_certificate_transfer_relation(self) -> int:
        relation_name = "certificates"
        remote_app_name = "certificate-transfer-provider"
        relation_id = self.harness.add_relation(
            relation_name=relation_name,
            remote_app=remote_app_name,
        )
        return relation_id

    @patch(f"{BASE_CHARM_DIR}._on_certificate_available")
    def test_given_certificates_in_relation_data_when_relation_changed_then_certificate_available_event_is_emitted(
        self, mock_certificate_available: MagicMock
    ):
        remote_unit_name = "certificate-transfer-provider/0"
        relation_id = self.create_certificate_transfer_relation()
        self.harness.add_relation_unit(relation_id=relation_id, remote_unit_name=remote_unit_name)
        certificate = "whatever certificate"
        ca = "whatever CA certificate"
        chain = ["cert1", "cert2"]
        chain_string = json.dumps(chain)
        key_values = {
            "certificate": certificate,
            "ca": ca,
            "chain": chain_string,
            "relation_id": str(relation_id),
        }
        self.harness.update_relation_data(
            relation_id=relation_id, app_or_unit=remote_unit_name, key_values=key_values
        )

        args, _ = mock_certificate_available.call_args
        certificate_available_event = args[0]
        assert certificate_available_event.certificate == certificate
        assert certificate_available_event.ca == ca
        assert certificate_available_event.chain == chain
        assert certificate_available_event.relation_id == relation_id

    @patch(f"{BASE_CHARM_DIR}._on_certificate_available")
    def test_given_only_certificate_in_relation_data_when_relation_changed_then_certificate_available_event_is_emitted(
        self, mock_certificate_available: MagicMock
    ):
        remote_unit_name = "certificate-transfer-provider/0"
        relation_id = self.create_certificate_transfer_relation()
        self.harness.add_relation_unit(relation_id=relation_id, remote_unit_name=remote_unit_name)
        certificate = "whatever certificate"
        key_values = {
            "certificate": certificate,
            "relation_id": str(relation_id),
        }
        self.harness.update_relation_data(
            relation_id=relation_id, app_or_unit=remote_unit_name, key_values=key_values
        )

        args, _ = mock_certificate_available.call_args
        certificate_available_event = args[0]
        assert certificate_available_event.certificate == certificate
        assert certificate_available_event.ca is None
        assert certificate_available_event.chain is None
        assert certificate_available_event.relation_id == relation_id

    def test_given_none_of_the_expected_keys_in_relation_data_when_relation_changed_then_warning_log_is_emitted(
        self,
    ):
        remote_unit_name = "certificate-transfer-provider/0"
        relation_id = self.create_certificate_transfer_relation()
        self.harness.add_relation_unit(relation_id=relation_id, remote_unit_name=remote_unit_name)
        key_values = {
            "banana": "whatever banana content",
            "pizza": "whatever pizza content",
        }

        with self.assertLogs(BASE_LIB_DIR, level="WARNING") as log:
            self.harness.update_relation_data(
                relation_id=relation_id, app_or_unit=remote_unit_name, key_values=key_values
            )

        assert "Provider relation data did not pass JSON Schema validation" in log.output[0]

    def test_given_provider_uses_application_relation_data_when_relation_changed_then_log_is_emitted(
        self,
    ):
        relation_id = self.create_certificate_transfer_relation()
        key_values = {"certificate": "whatever cert"}
        with self.assertLogs(BASE_LIB_DIR, level="INFO") as log:
            self.harness.update_relation_data(
                relation_id=relation_id,
                app_or_unit="certificate-transfer-provider",
                key_values=key_values,
            )

        assert "No remote unit in relation" in log.output[0]

    @patch(f"{BASE_CHARM_DIR}._on_certificate_removed")
    def test_given_certificate_in_relation_data_when_relation_broken_then_certificate_removed_event_is_emitted(
        self,
        mock_on_certificate_removed: MagicMock,
    ):
        remote_unit_name = "certificate-transfer-provider/0"
        relation_id = self.create_certificate_transfer_relation()
        self.harness.add_relation_unit(relation_id=relation_id, remote_unit_name=remote_unit_name)
        self.harness.remove_relation(relation_id)

        mock_on_certificate_removed.assert_called()

    def test_given_invalid_relation_data_when_is_ready_then_false_is_returned(self):
        remote_unit_name = "certificate-transfer-provider/0"
        relation_id = self.create_certificate_transfer_relation()
        self.harness.add_relation_unit(relation_id=relation_id, remote_unit_name=remote_unit_name)
        key_values = {
            "banana": "whatever banana content",
            "pizza": "whatever pizza content",
        }
        self.harness.update_relation_data(
            relation_id=relation_id, app_or_unit=remote_unit_name, key_values=key_values
        )
        relation = self.harness.model.get_relation(
            relation_name="certificates", relation_id=relation_id
        )
        assert relation
        assert not self.harness.charm.certificate_transfer.is_ready(relation)

    def test_given_valid_relation_data_when_is_ready_then_true_is_returned(self):
        relation_id = self.create_certificate_transfer_relation()
        relation = self.harness.model.get_relation(
            relation_name="certificates", relation_id=relation_id
        )
        self.harness.add_relation_unit(
            relation_id=relation_id, remote_unit_name="certificate-transfer-provider/0"
        )
        certificate = "whatever certificate"
        key_values = {
            "certificate": certificate,
            "relation_id": str(relation_id),
        }
        self.harness.update_relation_data(
            relation_id=relation_id,
            app_or_unit="certificate-transfer-provider",
            key_values=key_values,
        )
        assert relation
        assert self.harness.charm.certificate_transfer.is_ready(relation)
