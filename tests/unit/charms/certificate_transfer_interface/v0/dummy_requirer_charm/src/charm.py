# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

from ops.charm import CharmBase
from ops.main import main

from lib.charms.certificate_transfer_interface.v0.certificate_transfer import (
    CertificateAvailableEvent,
    CertificateTransferRequires,
)


class DummyCertificateTransferRequirerCharm(CharmBase):
    def __init__(self, *args):
        super().__init__(*args)
        self.certificate_transfer = CertificateTransferRequires(self, "certificates")
        self.framework.observe(
            self.certificate_transfer.on.certificate_available, self._on_certificate_available
        )

    def _on_certificate_available(self, event: CertificateAvailableEvent):
        pass


if __name__ == "__main__":
    main(DummyCertificateTransferRequirerCharm)
