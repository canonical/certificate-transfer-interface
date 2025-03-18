# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

from typing import Any

from ops.charm import ActionEvent, CharmBase
from ops.main import main

from lib.charms.certificate_transfer_interface.v0.certificate_transfer import (
    CertificateAvailableEvent,
    CertificateRemovedEvent,
    CertificateTransferRequires,
)


class DummyCertificateTransferRequirerCharm(CharmBase):
    def __init__(self, *args: Any):
        super().__init__(*args)
        self.certificate_transfer = CertificateTransferRequires(self, "certificates")
        self.framework.observe(
            self.certificate_transfer.on.certificate_available, self._on_certificate_available
        )
        self.framework.observe(
            self.certificate_transfer.on.certificate_removed, self._on_certificate_removed
        )
        self.framework.observe(self.on.is_ready_action, self._on_is_ready_action)

    def _on_certificate_available(self, _: CertificateAvailableEvent):
        pass

    def _on_certificate_removed(self, _: CertificateRemovedEvent):
        pass

    def _on_is_ready_action(self, event: ActionEvent):
        rel = self.model.get_relation("certificates", int(event.params["relation-id"]))
        if rel:
            event.set_results({"ready": self.certificate_transfer.is_ready(rel)})
        else:
            event.set_results({"ready": False})


if __name__ == "__main__":
    main(DummyCertificateTransferRequirerCharm)
