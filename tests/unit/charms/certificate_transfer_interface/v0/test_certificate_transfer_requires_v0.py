# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

import json
import unittest
from pathlib import Path

import pytest
import yaml
from ops.testing import Context, JujuLogLine, Relation, State

from lib.charms.certificate_transfer_interface.v0.certificate_transfer import (
    CertificateAvailableEvent,
    CertificateRemovedEvent,
)
from tests.unit.charms.certificate_transfer_interface.v0.dummy_requirer_charm.src.charm import (
    DummyCertificateTransferRequirerCharm,
)

APP_NAME = "certificates-transfer-interface-requirer"
BASE_LIB_DIR = "lib.charms.certificate_transfer_interface.v0.certificate_transfer"
BASE_CHARM_DIR = "tests.unit.charms.certificate_transfer_interface.v0.dummy_requirer_charm.src.charm.DummyCertificateTransferRequirerCharm"

METADATA = yaml.safe_load(
    Path(
        "tests/unit/charms/certificate_transfer_interface/v0/dummy_requirer_charm/metadata.yaml"
    ).read_text()
)
ENDPOINT = "certificates"
INTERFACE = "certificate_transfer"


class TestCertificateTransferRequiresV0(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def context(self):
        self.ctx = Context(
            charm_type=DummyCertificateTransferRequirerCharm,
            meta=METADATA,
            actions=METADATA.get("actions", {}),
        )

    def test_given_is_leader_when_relation_created_then_version_is_added_to_app_databag(self):
        relation = Relation(
            endpoint=ENDPOINT,
            interface=INTERFACE,
        )
        state_in = State(leader=True, relations=[relation])

        state_out = self.ctx.run(self.ctx.on.relation_created(relation), state_in)

        relation_out = state_out.get_relation(relation.id)
        assert relation_out
        assert relation_out.local_app_data.get("version", "wrong") == "0"

    def test_given_certificates_in_relation_data_when_relation_changed_then_certificate_available_event_is_emitted(
        self,
    ):
        certificate = "whatever certificate"
        ca = "whatever CA certificate"
        chain = ["cert1", "cert2"]
        chain_string = json.dumps(chain)
        key_values = {
            "certificate": certificate,
            "ca": ca,
            "chain": chain_string,
        }
        relation = Relation(
            endpoint=ENDPOINT, interface=INTERFACE, remote_units_data={0: key_values}
        )
        state_in = State(leader=True, relations=[relation])

        self.ctx.run(self.ctx.on.relation_changed(relation), state_in)

        last_event = self.ctx.emitted_events[-1]
        assert isinstance(last_event, CertificateAvailableEvent)
        assert last_event.certificate == certificate
        assert last_event.ca == ca
        assert last_event.chain == chain

    def test_given_only_certificate_in_relation_data_when_relation_changed_then_certificate_available_event_is_emitted(
        self,
    ):
        certificate = "whatever certificate"
        key_values = {
            "certificate": certificate,
        }
        relation = Relation(
            endpoint=ENDPOINT, interface=INTERFACE, remote_units_data={0: key_values}
        )
        state_in = State(leader=True, relations=[relation])

        self.ctx.run(self.ctx.on.relation_changed(relation), state_in)

        last_event = self.ctx.emitted_events[-1]
        assert isinstance(last_event, CertificateAvailableEvent)
        assert last_event.certificate == certificate

    def test_given_none_of_the_expected_keys_in_relation_data_when_relation_changed_then_warning_log_is_emitted(
        self,
    ):
        key_values = {
            "banana": "whatever banana content",
            "pizza": "whatever pizza content",
        }
        relation = Relation(
            endpoint=ENDPOINT, interface=INTERFACE, remote_units_data={0: key_values}
        )
        state_in = State(leader=True, relations=[relation])

        self.ctx.run(self.ctx.on.relation_changed(relation), state_in)

        assert (
            JujuLogLine(
                level="WARNING",
                message="Provider relation data did not pass JSON Schema validation: {'banana': 'whatever banana content', 'pizza': 'whatever pizza content'}",
            )
            in self.ctx.juju_log
        )

    def test_given_provider_uses_application_relation_data_when_relation_changed_then_log_is_emitted(
        self,
    ):
        key_values = {"certificate": "whatever cert"}
        relation = Relation(
            endpoint=ENDPOINT,
            interface=INTERFACE,
            remote_app_data=key_values,
            remote_units_data={},
        )
        state_in = State(leader=True, relations=[relation])

        self.ctx.run(self.ctx.on.relation_changed(relation), state_in)

        assert (
            JujuLogLine(
                level="INFO",
                message=f"No remote unit in relation: {ENDPOINT}",
            )
            in self.ctx.juju_log
        )

    def test_given_certificate_in_relation_data_when_relation_broken_then_certificate_removed_event_is_emitted(
        self,
    ):
        certificate = "whatever certificate"
        ca = "whatever CA certificate"
        chain = ["cert1", "cert2"]
        chain_string = json.dumps(chain)
        key_values = {
            "certificate": certificate,
            "ca": ca,
            "chain": chain_string,
        }
        relation = Relation(
            endpoint=ENDPOINT, interface=INTERFACE, remote_units_data={0: key_values}
        )
        state_in = State(leader=True, relations=[relation])

        self.ctx.run(self.ctx.on.relation_broken(relation), state_in)

        last_event = self.ctx.emitted_events[-1]
        assert isinstance(last_event, CertificateRemovedEvent)

    def test_given_invalid_relation_data_when_is_ready_then_false_is_returned(self):
        key_values = {
            "banana": "whatever banana content",
            "pizza": "whatever pizza content",
        }
        relation = Relation(
            endpoint=ENDPOINT, interface=INTERFACE, remote_units_data={0: key_values}
        )
        state_in = State(leader=True, relations=[relation])

        self.ctx.run(
            self.ctx.on.action("is-ready", params={"relation-id": str(relation.id)}), state_in
        )

        assert self.ctx.action_results
        assert not self.ctx.action_results["ready"]

    def test_given_valid_relation_data_when_is_ready_then_true_is_returned(self):
        key_values = {"certificate": "whatever cert"}
        relation = Relation(
            endpoint=ENDPOINT, interface=INTERFACE, remote_units_data={0: key_values}
        )
        state_in = State(leader=True, relations=[relation])

        self.ctx.run(
            self.ctx.on.action("is-ready", params={"relation-id": str(relation.id)}), state_in
        )

        assert self.ctx.action_results
        assert self.ctx.action_results["ready"]
