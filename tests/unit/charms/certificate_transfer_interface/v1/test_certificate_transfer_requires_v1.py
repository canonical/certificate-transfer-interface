# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

import json

import pytest
import scenario
from ops.charm import ActionEvent, CharmBase

from lib.charms.certificate_transfer_interface.v1.certificate_transfer import (
    CertificatesAvailableEvent,
    CertificatesRemovedEvent,
    CertificateTransferRequires,
)


class DummyCertificateTransferRequirerCharm(CharmBase):
    def __init__(self, *args):
        super().__init__(*args)
        self.certificate_transfer = CertificateTransferRequires(self, "certificate_transfer")
        self.framework.observe(
            self.on.get_all_certificates_action, self._on_get_all_certificates_action
        )

    def _on_get_all_certificates_action(self, event: ActionEvent):
        relation_id = event.params.get("relation-id", None)
        certificates = self.certificate_transfer.get_all_certificates(
            relation_id=int(relation_id) if relation_id else None
        )
        event.set_results({"certificates": certificates})


class TestCertificateTransferRequiresV1:
    @pytest.fixture(autouse=True)
    def context(self):
        self.ctx = scenario.Context(
            charm_type=DummyCertificateTransferRequirerCharm,
            meta={
                "name": "certificate-transfer-requirer",
                "requires": {"certificate_transfer": {"interface": "certificate_transfer"}},
            },
            actions={
                "get-all-certificates": {
                    "params": {
                        "relation-id": {"type": "string"},
                    },
                },
            },
        )

    def test_given_certificates_in_relation_data_when_relation_changed_then_certificate_available_event_is_emitted(  # noqa: E501
        self,
    ):
        relation = scenario.Relation(
            endpoint="certificate_transfer",
            interface="certificate_transfer",
            remote_app_data={"certificates": json.dumps(["cert1"])},
        )
        state_in = scenario.State(relations=[relation])

        self.ctx.run(relation.changed_event, state_in)

        assert len(self.ctx.emitted_events) == 2
        assert isinstance(self.ctx.emitted_events[1], CertificatesAvailableEvent)
        assert self.ctx.emitted_events[1].certificates == {"cert1"}
        assert self.ctx.emitted_events[1].relation_id == relation.relation_id

    def test_given_none_of_the_expected_keys_in_relation_data_when_relation_changed_then_certificate_available_event_emitted_with_empty_cert(  # noqa: E501
        self, caplog
    ):
        relation = scenario.Relation(
            endpoint="certificate_transfer",
            interface="certificate_transfer",
            remote_app_data={"bad-key": json.dumps(["cert1"])},
        )
        state_in = scenario.State(relations=[relation])

        self.ctx.run(relation.changed_event, state_in)

        assert len(self.ctx.emitted_events) == 2
        assert isinstance(self.ctx.emitted_events[1], CertificatesAvailableEvent)
        assert self.ctx.emitted_events[1].certificates == set()
        assert self.ctx.emitted_events[1].relation_id == relation.relation_id

    def test_given_certificates_in_relation_data_when_relation_removed_then_certificates_removed_event_is_emitted(  # noqa: E501
        self, caplog: pytest.LogCaptureFixture
    ):
        relation = scenario.Relation(
            endpoint="certificate_transfer",
            interface="certificate_transfer",
            remote_app_data={"certificates": json.dumps(["cert1"])},
        )
        state_in = scenario.State(relations=[relation])

        self.ctx.run(relation.broken_event, state_in)

        assert len(self.ctx.emitted_events) == 2
        assert isinstance(self.ctx.emitted_events[1], CertificatesRemovedEvent)
        assert self.ctx.emitted_events[1].relation_id == relation.relation_id

    def test_given_no_relation_available_when_get_all_certificates_then_empty_set_returned(self):
        state_in = scenario.State()
        action = scenario.Action(name="get-all-certificates")

        action_output = self.ctx.run_action(action, state_in)

        assert action_output.success
        assert action_output.results == {"certificates": set()}

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
            remote_app_data={"certificates": databag_value},
        )
        state_in = scenario.State(leader=True, relations=[relation])

        self.ctx.run(relation.changed_event, state_in)

        logs = [(record.levelname, record.module, record.message) for record in caplog.records]
        assert (
            "ERROR",
            "certificate_transfer",
            error_msg,
        ) in logs
