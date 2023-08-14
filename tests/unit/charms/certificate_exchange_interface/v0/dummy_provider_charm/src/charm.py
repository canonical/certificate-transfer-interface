# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

from ops.charm import CharmBase, RelationJoinedEvent
from ops.main import main

from lib.charms.certificate_exchange_interface.v0.certificate_exchange import (
    CertificateExchangeProvides,
)


class DummyCertificateExchangeProviderCharm(CharmBase):
    def __init__(self, *args):
        super().__init__(*args)
        self.certificate_exchange = CertificateExchangeProvides(self, "certificates")
        self.framework.observe(
            self.on.certificates_relation_joined, self._on_certificates_relation_joined
        )

    def _on_certificates_relation_joined(self, event: RelationJoinedEvent):
        certificate = "my certificate"
        ca = "my CA certificate"
        chain = ["certificate 1", "certificate 2"]
        self.certificate_exchange.set_certificate(certificate=certificate, ca=ca, chain=chain)


if __name__ == "__main__":
    main(DummyCertificateExchangeProviderCharm)
