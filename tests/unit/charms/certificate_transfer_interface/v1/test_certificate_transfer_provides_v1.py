# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

import json

import pytest
from ops import testing

from tests.unit.charms.certificate_transfer_interface.v1.dummy_provider_charm.src.charm import (
    DummyCertificateTransferProviderCharm,
)

BASE_LIB_DIR = "lib.charms.certificate_transfer_interface.v1.certificate_transfer"
APP_NAME = "certificate-transfer-interface-provider"


class TestCertificateTransferProvidesV1:
    @pytest.fixture(scope="function", autouse=True)
    def setUp(self):
        self.unit_name = "certificate-transfer-interface-provider/0"
        self.harness = testing.Harness(DummyCertificateTransferProviderCharm)
        self.harness.begin()
        yield
        self.harness.cleanup()

    def create_certificate_transfer_relation(self) -> int:
        relation_name = "certificates"
        remote_app_name = "certificate-transfer-requirer"
        relation_id = self.harness.add_relation(
            relation_name=relation_name,
            remote_app=remote_app_name,
        )
        return relation_id

    @pytest.mark.parametrize("relation_id", [None, 2])
    def test_given_unavailable_relations_when_adding_certificates_then_error_is_logged(
        self, caplog: pytest.LogCaptureFixture, relation_id
    ):
        certificate = "certificate"
        self.harness.set_leader()
        self.harness.charm.certificate_transfer.add_certificates({certificate}, relation_id)
        logs = [(record.levelname, record.module, record.message) for record in caplog.records]
        assert (
            "ERROR",
            "certificate_transfer",
            "At least 1 matching relation ID not found with the relation name 'certificates'",
        ) in logs

    @pytest.mark.parametrize("relation_id,expected_relations", [(None, [0, 1, 2]), (2, [2])])
    def test_given_multiple_relations_when_adding_certificates_then_certificates_sent(
        self, relation_id, expected_relations
    ):
        num_relations = 3
        relation_ids = [self.create_certificate_transfer_relation() for _ in range(num_relations)]
        certificate_1 = "-----begin certificate 1-----"
        certificate_2 = "-----begin certificate 2-----"
        self.harness.set_leader()
        self.harness.charm.certificate_transfer.add_certificates(
            {certificate_1, certificate_2}, relation_id
        )

        relation_datas = [
            self.harness.get_relation_data(
                relation_id=relation_ids[i],
                app_or_unit=APP_NAME,
            )
            for i in range(num_relations)
        ]

        for ex in expected_relations:
            assert relation_datas[ex].get("certificates") == json.dumps(
                list({certificate_1, certificate_2})
            )

    @pytest.mark.parametrize("relation_id", [None, 2])
    def test_given_unavailable_relations_when_removing_certificates_then_error_is_logged(
        self, caplog: pytest.LogCaptureFixture, relation_id
    ):
        certificate = "certificate"
        self.harness.set_leader()
        self.harness.charm.certificate_transfer.remove_certificate(certificate, relation_id)
        logs = [(record.levelname, record.module, record.message) for record in caplog.records]
        assert (
            "ERROR",
            "certificate_transfer",
            "At least 1 matching relation ID not found with the relation name 'certificates'",
        ) in logs

    @pytest.mark.parametrize("relation_id,expected_relations", [(None, [0, 1, 2]), (2, [2])])
    def test_given_multiple_relations_when_removing_certificates_then_certificates_removed(
        self, relation_id, expected_relations
    ):
        num_relations = 3
        relation_ids = [self.create_certificate_transfer_relation() for _ in range(num_relations)]

        certificate_1 = "-----begin certificate 1-----"
        certificate_2 = "-----begin certificate 2-----"
        self.harness.set_leader()
        self.harness.charm.certificate_transfer.add_certificates({certificate_1, certificate_2})

        self.harness.charm.certificate_transfer.remove_certificate(certificate_1, relation_id)

        relation_datas = [
            self.harness.get_relation_data(
                relation_id=relation_ids[i],
                app_or_unit="certificate-transfer-interface-provider",
            )
            for i in range(num_relations)
        ]

        for i in range(num_relations):
            if i in expected_relations:
                assert relation_datas[i].get("certificates") == json.dumps(list({certificate_2}))
            else:
                assert relation_datas[i].get("certificates") == json.dumps(
                    list({certificate_1, certificate_2})
                )

    @pytest.mark.parametrize(
        "databag_value,error_msg",
        [
            (
                '"some string"',
                """('Error parsing relation databag: ('failed to validate databag: \
{\\'certificates\\': \\'"some string"\\'}',). ', 'Make sure not to interact with the\
 databags except using the public methods in the provider library and use version V1.')""",
            ),
            (
                "unloadable",
                """('Error parsing relation databag: ("invalid databag contents: \
expecting json. {'certificates': 'unloadable'}",). ', 'Make sure not to interact with \
the databags except using the public methods in the provider library and use version V1.')""",
            ),
        ],
    )
    def test_given_broken_relation_databag_when_set_certificate_then_error_is_logged(
        self, caplog, databag_value, error_msg
    ):
        relation_id = self.create_certificate_transfer_relation()
        self.harness.set_leader()
        self.harness.update_relation_data(
            relation_id=relation_id,
            app_or_unit=APP_NAME,
            key_values={"certificates": databag_value},
        )

        self.harness.charm.certificate_transfer.add_certificates({"-----BEGIN CERTIFICATE-----"})

        logs = [(record.levelname, record.module, record.message) for record in caplog.records]
        assert (
            "ERROR",
            "certificate_transfer",
            error_msg,
        ) in logs
