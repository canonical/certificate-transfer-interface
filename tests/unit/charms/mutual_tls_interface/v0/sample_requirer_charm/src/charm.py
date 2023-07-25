# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

from ops.charm import CharmBase
from ops.main import main

from lib.charms.mutual_tls_interface.v0.mutual_tls import (
    CertificateAvailableEvent,
    MutualTLSRequires,
)


class SampleMutualTLSRequirerCharm(CharmBase):
    def __init__(self, *args):
        super().__init__(*args)
        self.mutual_tls = MutualTLSRequires(self, "certificates")
        self.framework.observe(
            self.mutual_tls.on.certificate_available, self._on_certificate_available
        )

    def _on_certificate_available(self, event: CertificateAvailableEvent):
        print(event.certificate)
        print(event.ca)
        print(event.chain)


if __name__ == "__main__":
    main(SampleMutualTLSRequirerCharm)
