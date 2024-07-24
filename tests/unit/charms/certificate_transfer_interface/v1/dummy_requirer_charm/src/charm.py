# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

import logging

from ops.charm import CharmBase
from ops.main import main

from lib.charms.certificate_transfer_interface.v1.certificate_transfer import (
    CertificatesAvailableEvent,
    CertificatesRemovedEvent,
    CertificateTransferRequires,
)


class DummyCertificateTransferRequirerCharm(CharmBase):
    def __init__(self, *args):
        super().__init__(*args)
        self.certificate_transfer = CertificateTransferRequires(self, "certificates")
        self.framework.observe(
            self.certificate_transfer.on.certificate_set_updated, self._on_certificates_available
        )
        self.framework.observe(
            self.certificate_transfer.on.certificates_removed, self._on_certificates_removed
        )

    def _on_certificates_available(self, event: CertificatesAvailableEvent):
        logging.info(event.certificates)
        logging.info(event.relation_id)

    def _on_certificates_removed(self, event: CertificatesRemovedEvent):
        logging.info(event.relation_id)


if __name__ == "__main__":
    main(DummyCertificateTransferRequirerCharm)
