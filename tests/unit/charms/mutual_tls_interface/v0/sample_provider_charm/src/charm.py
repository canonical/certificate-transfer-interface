# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

from ops.charm import CharmBase, RelationJoinedEvent
from ops.main import main

from lib.charms.mutual_tls_interface.v0.mutual_tls import MutualTLSProvides


class SampleMutualTLSProviderCharm(CharmBase):
    def __init__(self, *args):
        super().__init__(*args)
        self.mutual_tls = MutualTLSProvides(self, "certificates")
        self.framework.observe(
            self.on.certificates_relation_joined, self._on_certificates_relation_joined
        )

    def _on_certificates_relation_joined(self, event: RelationJoinedEvent):
        certificate = "my certificate"
        ca = "my CA certificate"
        chain = ["certificate 1", "certificate 2"]
        self.mutual_tls.set_certificate(certificate=certificate, ca=ca, chain=chain)


if __name__ == "__main__":
    main(SampleMutualTLSProviderCharm)
