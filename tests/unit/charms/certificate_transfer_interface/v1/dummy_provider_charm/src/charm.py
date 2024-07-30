# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

from ops.charm import CharmBase, RelationJoinedEvent
from ops.main import main

from lib.charms.certificate_transfer_interface.v1.certificate_transfer import (
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
        self.certificate_transfer.add_certificates({certificate})


if __name__ == "__main__":
    main(DummyCertificateTransferProviderCharm)
