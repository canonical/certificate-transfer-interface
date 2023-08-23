# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

from ops.charm import CharmBase, RelationJoinedEvent
from ops.main import main

from lib.charms.certificate_transfer_interface.v0.certificate_transfer import (
    CertificateTransferProvides,
)


class DummyCertificateTransferProviderCharm(CharmBase):
    def __init__(self, *args):
        super().__init__(*args)
        self.certificate_transfer = CertificateTransferProvides(self, "certificates")
        self.framework.observe(
            self.on.certificates_relation_joined, self._on_certificates_relation_joined
        )

    def _on_certificates_relation_joined(self, event: RelationJoinedEvent):
        certificate = "my certificate"
        ca = "my CA certificate"
        chain = ["certificate 1", "certificate 2"]
        self.certificate_transfer.set_certificate(
            certificate=certificate, ca=ca, chain=chain, relation_id=event.relation.id
        )


if __name__ == "__main__":
    main(DummyCertificateTransferProviderCharm)
