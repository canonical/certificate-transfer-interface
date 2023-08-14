# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

from ops.charm import CharmBase
from ops.main import main

from lib.charms.certificate_exchange_interface.v1.certificate_exchange import (
    CertificateAvailableEvent,
    CertificateExchangeRequires,
)


class DummyCertificateExchangeRequirerCharm(CharmBase):
    def __init__(self, *args):
        super().__init__(*args)
        self.certificate_exchange = CertificateExchangeRequires(self, "certificates")
        self.framework.observe(
            self.certificate_exchange.on.certificate_available, self._on_certificate_available
        )

    def _on_certificate_available(self, event: CertificateAvailableEvent):
        print(event.certificate)
        print(event.ca)
        print(event.chain)


if __name__ == "__main__":
    main(DummyCertificateExchangeRequirerCharm)
