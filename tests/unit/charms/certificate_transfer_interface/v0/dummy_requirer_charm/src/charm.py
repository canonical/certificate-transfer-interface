# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

from ops.charm import CharmBase
from ops.main import main

from lib.charms.certificate_transfer_interface.v0.certificate_transfer import (
    CertificateAvailableEvent,
    CertificateRemovedEvent,
    CertificateTransferRequires,
)


class DummyCertificateTransferRequirerCharm(CharmBase):
    def __init__(self, *args):
        super().__init__(*args)
        self.certificate_transfer = CertificateTransferRequires(self, "certificates")
        self.framework.observe(
            self.certificate_transfer.on.certificate_available, self._on_certificate_available
        )
        self.framework.observe(
            self.certificate_transfer.on.certificate_removed, self._on_certificate_removed
        )

    def _on_certificate_available(self, event: CertificateAvailableEvent):
        pass

    def _on_certificate_removed(self, event: CertificateRemovedEvent):
        pass


if __name__ == "__main__":
    main(DummyCertificateTransferRequirerCharm)
