# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

import json

import pytest
import scenario
from ops.charm import ActionEvent, CharmBase

from lib.charms.certificate_transfer_interface.v1.certificate_transfer import (
    CertificateTransferProvides,
)


class DummyCertificateTransferProviderCharm(CharmBase):
    def __init__(self, *args):
        super().__init__(*args)
        self.certificate_transfer = CertificateTransferProvides(self, "certificate_transfer")
        self.framework.observe(self.on.add_certificates_action, self._on_add_certificates_action)
        self.framework.observe(
            self.on.remove_certificate_action, self._on_remove_certificate_action
        )

    def _on_add_certificates_action(self, event: ActionEvent):
        certificates = event.params.get("certificates")
        relation_id = event.params.get("relation-id", None)
        assert certificates
        certificates = set(certificates.split(", "))
        self.certificate_transfer.add_certificates(
            certificates=certificates, relation_id=int(relation_id) if relation_id else None
        )

    def _on_remove_certificate_action(self, event: ActionEvent):
        certificate = event.params.get("certificate")
        relation_id = event.params.get("relation-id", None)
        assert certificate
        self.certificate_transfer.remove_certificate(
            certificate=certificate, relation_id=int(relation_id) if relation_id else None
        )


class TestCertificateTransferProvidesV1:
    @pytest.fixture(autouse=True)
    def context(self):
        self.ctx = scenario.Context(
            charm_type=DummyCertificateTransferProviderCharm,
            meta={
                "name": "certificate-transfer-provider",
                "provides": {"certificate_transfer": {"interface": "certificate_transfer"}},
            },
            actions={
                "add-certificates": {
                    "params": {
                        "certificates": {"type": "string"},
                        "relation-id": {"type": "string"},
                    },
                },
                "remove-certificate": {
                    "params": {
                        "certificate": {"type": "string"},
                        "relation-id": {"type": "string"},
                    },
                },
            },
        )

    def test_given_no_relation_when_add_certificate_then_error_is_logged(
        self, caplog: pytest.LogCaptureFixture
    ):
        state_in = scenario.State(leader=True)

        self.ctx.run(
            self.ctx.on.action("add-certificates", params={"certificates": "certificate"}),
            state_in,
        )

        logs = [(record.levelname, record.module, record.message) for record in caplog.records]
        assert (
            "ERROR",
            "certificate_transfer",
            "At least 1 matching relation ID not found with the relation name 'certificate_transfer'",  # noqa: E501
        ) in logs

    @pytest.mark.skip(reason="https://github.com/canonical/ops-scenario/issues/193")
    def test_given_unrelated_relation_when_add_certificates_then_error_is_logged(
        self, caplog: pytest.LogCaptureFixture
    ):
        relation = scenario.Relation(
            endpoint="certificate_transfer", interface="certificate_transfer"
        )
        state_in = scenario.State(leader=True, relations=[relation])

        self.ctx.run(
            self.ctx.on.action(
                "add-certificates",
                params={
                    "certificates": "certificate",
                    "relation-id": str(relation.id + 1),  # non-existent relation id
                },
            ),
            state_in,
        )

        logs = [(record.levelname, record.module, record.message) for record in caplog.records]
        assert (
            "ERROR",
            "certificate_transfer",
            "At least 1 matching relation ID not found with the relation name 'certificate_transfer'",  # noqa: E501
        ) in logs

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
        relation = scenario.Relation(
            endpoint="certificate_transfer",
            interface="certificate_transfer",
            local_app_data={"certificates": databag_value},
        )
        state_in = scenario.State(leader=True, relations=[relation])

        self.ctx.run(
            self.ctx.on.action(
                "add-certificates",
                params={
                    "certificates": "certificate",
                    "relation-id": str(relation.id),
                },
            ),
            state_in,
        )

        logs = [(record.levelname, record.module, record.message) for record in caplog.records]
        assert (
            "ERROR",
            "certificate_transfer",
            error_msg,
        ) in logs

    def test_given_multiple_relations_when_add_certificates_then_certificates_sent_to_all_relations(  # noqa: E501
        self,
    ):
        relation_1 = scenario.Relation(
            endpoint="certificate_transfer", interface="certificate_transfer"
        )
        relation_2 = scenario.Relation(
            endpoint="certificate_transfer", interface="certificate_transfer"
        )
        relation_3 = scenario.Relation(
            endpoint="certificate_transfer", interface="certificate_transfer"
        )
        state_in = scenario.State(leader=True, relations=[relation_1, relation_2, relation_3])

        state_out = self.ctx.run(
            self.ctx.on.action(
                "add-certificates",
                params={
                    "certificates": "certificate1, certificate2",
                },
            ),
            state_in,
        )

        certificates_relation_1 = state_out.get_relation(relation_1.id).local_app_data[
            "certificates"
        ]
        certificates_relation_2 = state_out.get_relation(relation_2.id).local_app_data[
            "certificates"
        ]
        certificates_relation_3 = state_out.get_relation(relation_3.id).local_app_data[
            "certificates"
        ]
        assert set(json.loads(certificates_relation_1)) == {"certificate1", "certificate2"}
        assert set(json.loads(certificates_relation_2)) == {"certificate1", "certificate2"}
        assert set(json.loads(certificates_relation_3)) == {"certificate1", "certificate2"}

    def test_given_multiple_relations_when_add_certificates_with_relation_id_then_certificate_sent_to_specific_relation(  # noqa: E501
        self,
    ):
        relation_1 = scenario.Relation(
            endpoint="certificate_transfer", interface="certificate_transfer"
        )
        relation_2 = scenario.Relation(
            endpoint="certificate_transfer", interface="certificate_transfer"
        )
        relation_3 = scenario.Relation(
            endpoint="certificate_transfer", interface="certificate_transfer"
        )
        state_in = scenario.State(leader=True, relations=[relation_1, relation_2, relation_3])

        state_out = self.ctx.run(
            self.ctx.on.action(
                "add-certificates",
                params={
                    "certificates": "certificate1, certificate2",
                    "relation-id": str(relation_2.id),
                },
            ),
            state_in,
        )

        relation_1_app_data = state_out.get_relation(relation_1.id).local_app_data
        assert "certificates" not in relation_1_app_data
        relation_2_app_data = state_out.get_relation(relation_2.id).local_app_data
        assert set(json.loads(relation_2_app_data["certificates"])) == {
            "certificate1",
            "certificate2",
        }
        relation_3_app_data = state_out.get_relation(relation_3.id).local_app_data
        assert "certificates" not in relation_3_app_data

    def test_given_no_relation_when_remove_certificate_then_error_is_logged(
        self, caplog: pytest.LogCaptureFixture
    ):
        state_in = scenario.State(leader=True)

        self.ctx.run(
            self.ctx.on.action(
                "remove-certificate",
                params={"certificate": "certificate"},
            ),
            state_in,
        )

        logs = [(record.levelname, record.module, record.message) for record in caplog.records]
        assert (
            "ERROR",
            "certificate_transfer",
            "At least 1 matching relation ID not found with the relation name 'certificate_transfer'",  # noqa: E501
        ) in logs

    @pytest.mark.skip(reason="https://github.com/canonical/ops-scenario/issues/193")
    def test_given_unrelated_relation_when_remove_certificate_then_error_is_logged(
        self, caplog: pytest.LogCaptureFixture
    ):
        relation = scenario.Relation(
            endpoint="certificate_transfer", interface="certificate_transfer"
        )
        state_in = scenario.State(leader=True, relations=[relation])

        self.ctx.run(
            self.ctx.on.action(
                "remove-certificate",
                params={
                    "certificate": "certificate",
                    "relation-id": str(relation.id + 1),  # non-existent relation id
                },
            ),
            state_in,
        )

        logs = [(record.levelname, record.module, record.message) for record in caplog.records]
        assert (
            "ERROR",
            "certificate_transfer",
            "At least 1 matching relation ID not found with the relation name 'certificate_transfer'",  # noqa: E501
        ) in logs

    def test_given_multiple_relations_when_remove_certificate_then_certificate_removed_from_all_relations(  # noqa: E501
        self,
    ):
        relation_1 = scenario.Relation(
            endpoint="certificate_transfer",
            interface="certificate_transfer",
            local_app_data={"certificates": json.dumps(["certificate1", "certificate2"])},
        )
        relation_2 = scenario.Relation(
            endpoint="certificate_transfer",
            interface="certificate_transfer",
            local_app_data={"certificates": json.dumps(["certificate1", "certificate2"])},
        )
        relation_3 = scenario.Relation(
            endpoint="certificate_transfer",
            interface="certificate_transfer",
            local_app_data={"certificates": json.dumps(["certificate1", "certificate2"])},
        )
        state_in = scenario.State(leader=True, relations=[relation_1, relation_2, relation_3])

        state_out = self.ctx.run(
            self.ctx.on.action(
                "remove-certificate",
                params={
                    "certificate": "certificate1",
                },
            ),
            state_in,
        )

        certificates_relation_1 = state_out.get_relation(relation_1.id).local_app_data[
            "certificates"
        ]
        certificates_relation_2 = state_out.get_relation(relation_2.id).local_app_data[
            "certificates"
        ]
        certificates_relation_3 = state_out.get_relation(relation_3.id).local_app_data[
            "certificates"
        ]
        assert set(json.loads(certificates_relation_1)) == {"certificate2"}
        assert set(json.loads(certificates_relation_2)) == {"certificate2"}
        assert set(json.loads(certificates_relation_3)) == {"certificate2"}

    def test_given_multiple_relations_when_remove_certificate_with_relation_id_then_certificate_removed_from_specific_relation(  # noqa: E501
        self,
    ):
        relation_1 = scenario.Relation(
            endpoint="certificate_transfer",
            interface="certificate_transfer",
            local_app_data={"certificates": json.dumps(["certificate1", "certificate2"])},
        )
        relation_2 = scenario.Relation(
            endpoint="certificate_transfer",
            interface="certificate_transfer",
            local_app_data={"certificates": json.dumps(["certificate1", "certificate2"])},
        )
        relation_3 = scenario.Relation(
            endpoint="certificate_transfer",
            interface="certificate_transfer",
            local_app_data={"certificates": json.dumps(["certificate1", "certificate2"])},
        )
        state_in = scenario.State(leader=True, relations=[relation_1, relation_2, relation_3])

        state_out = self.ctx.run(
            self.ctx.on.action(
                "remove-certificate",
                params={
                    "certificate": "certificate1",
                    "relation-id": str(relation_2.id),
                },
            ),
            state_in,
        )

        relation_1_app_data = state_out.get_relation(relation_1.id).local_app_data
        assert set(json.loads(relation_1_app_data["certificates"])) == {
            "certificate1",
            "certificate2",
        }
        relation_2_app_data = state_out.get_relation(relation_2.id).local_app_data
        assert set(json.loads(relation_2_app_data["certificates"])) == {"certificate2"}
        relation_3_app_data = state_out.get_relation(relation_3.id).local_app_data
        assert set(json.loads(relation_3_app_data["certificates"])) == {
            "certificate1",
            "certificate2",
        }
