# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

import json
import unittest

from ops import testing

from tests.unit.charms.certificate_transfer_interface.v0.dummy_provider_charm.src.charm import (
    DummyCertificateTransferProviderCharm,
)

BASE_LIB_DIR = "lib.charms.certificate_transfer_interface.v0.certificate_transfer"


class TestCertificateTransferProvides(unittest.TestCase):
    def setUp(self):
        self.unit_name = "certificate-transfer-interface-provider/0"
        self.harness = testing.Harness(DummyCertificateTransferProviderCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()

    def create_certificate_transfer_relation(self) -> int:
        relation_name = "certificates"
        remote_app_name = "certificate-transfer-requirer"
        relation_id = self.harness.add_relation(
            relation_name=relation_name,
            remote_app=remote_app_name,
        )
        return relation_id

    def test_given_certificate_transfer_relation_exists_when_set_certificate_then_certificate_added_to_relation_data(  # noqa: E501
        self,
    ):
        relation_id = self.create_certificate_transfer_relation()

        certificate = "whatever cert"
        ca = "whatever ca"
        chain = ["whatever cert 1", "whatever cert 2"]

        self.harness.charm.certificate_transfer.set_certificate(
            certificate=certificate, ca=ca, chain=chain, relation_id=relation_id
        )

        relation_data = self.harness.get_relation_data(
            app_or_unit="certificate-transfer-interface-provider/0",
            relation_id=relation_id,
        )
        self.assertEqual(relation_data["certificate"], certificate)
        self.assertEqual(relation_data["ca"], ca)
        self.assertEqual(relation_data["chain"], json.dumps(chain))

    def test_given_wrong_relation_id_and_certificate_transfer_relation_exists_when_set_certificate_then_raises_key_error(  # noqa: E501
        self,
    ):
        relation_id = self.create_certificate_transfer_relation()
        relation_id = relation_id + 5
        certificate = "whatever cert"
        ca = "whatever ca"
        chain = ["whatever cert 1", "whatever cert 2"]
        with self.assertRaises(KeyError):
            self.harness.charm.certificate_transfer.set_certificate(
                certificate=certificate, ca=ca, chain=chain, relation_id=relation_id
            )

    def test_given_no_certificate_transfer_relation_when_set_certificate_then_runtime_error_is_raised(  # noqa: E501
        self,
    ):
        certificate = "whatever cert"
        ca = "whatever ca"
        chain = ["whatever cert 1", "whatever cert 2"]
        with self.assertRaises(RuntimeError) as error:
            self.harness.charm.certificate_transfer.set_certificate(
                certificate=certificate, ca=ca, chain=chain
            )
        self.assertEqual(str(error.exception), "relation_id should be provided.")

    def test_given_certificate_transfer_relation_exists_when_remove_certificate_then_certificate_removed_from_relation_data(  # noqa: E501
        self,
    ):
        relation_id = self.create_certificate_transfer_relation()
        relation_data = {
            "certificate": "whatever cert",
            "ca": "whatever ca",
            "chain": json.dumps(["cert 1", "cert 2"]),
        }
        self.harness.update_relation_data(
            relation_id=relation_id,
            key_values=relation_data,
            app_or_unit="certificate-transfer-interface-provider/0",
        )

        self.harness.charm.certificate_transfer.remove_certificate(relation_id=relation_id)

        relation_data = self.harness.get_relation_data(
            app_or_unit="certificate-transfer-interface-provider/0",
            relation_id=relation_id,
        )
        assert "certificate" not in relation_data
        assert "ca" not in relation_data
        assert "chain" not in relation_data

    def test_given_only_certificate_in_relation_data_when_remove_certificate_then_certificate_removed_from_relation_data(  # noqa: E501
        self,
    ):
        relation_id = self.create_certificate_transfer_relation()
        relation_data = {
            "certificate": "whatever cert",
        }
        self.harness.update_relation_data(
            relation_id=relation_id,
            key_values=relation_data,
            app_or_unit="certificate-transfer-interface-provider/0",
        )

        self.harness.charm.certificate_transfer.remove_certificate(relation_id=relation_id)

        relation_data = self.harness.get_relation_data(
            app_or_unit="certificate-transfer-interface-provider/0",
            relation_id=relation_id,
        )
        assert "certificate" not in relation_data

    def test_given_certificate_transfer_relation_exists_and_id_not_provided_when_remove_certificate_then_raises_run_time_error(  # noqa: E501
        self,
    ):
        relation_id = self.create_certificate_transfer_relation()
        relation_data = {
            "certificate": "whatever cert",
            "ca": "whatever ca",
            "chain": json.dumps(["cert 1", "cert 2"]),
        }
        self.harness.update_relation_data(
            relation_id=relation_id,
            key_values=relation_data,
            app_or_unit="certificate-transfer-interface-provider/0",
        )
        with self.assertRaises(RuntimeError) as error:
            self.harness.charm.certificate_transfer.remove_certificate()

        self.assertEqual(str(error.exception), "relation_id should be provided.")

    def test_given_certificate_transfer_relation_exists_and_wrong_relation_id_provided_when_remove_certificate_then_data_exists_in_relation(  # noqa: E501
        self,
    ):
        relation_id = self.create_certificate_transfer_relation()
        relation_data = {
            "certificate": "whatever cert",
            "ca": "whatever ca",
            "chain": json.dumps(["cert 1", "cert 2"]),
        }
        self.harness.update_relation_data(
            relation_id=relation_id,
            key_values=relation_data,
            app_or_unit="certificate-transfer-interface-provider/0",
        )
        relation_id = int(relation_id) + 2
        self.harness.charm.certificate_transfer.remove_certificate(relation_id=relation_id)
        assert "certificate" in relation_data
        assert "ca" in relation_data
        assert "chain" in relation_data

    def test_given_no_data_in_certificate_transfer_relation_when_remove_certificate_then_log_is_emitted(  # noqa: E501
        self,
    ):
        relation_id = self.create_certificate_transfer_relation()

        with self.assertLogs(BASE_LIB_DIR, level="WARNING") as log:
            self.harness.charm.certificate_transfer.remove_certificate(relation_id=relation_id)

        assert "Can't remove certificate - No certificate in relation data" in log.output[0]
