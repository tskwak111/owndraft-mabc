class OwnDraftError(Exception):
    """Base error with a stable machine-readable code and Korean detail."""

    code = "owndraft_error"

    def __init__(self, code: str | None = None, detail: str = "") -> None:
        self.detail = detail
        super().__init__(code or self.code)


class ContractError(OwnDraftError):
    code = "contract_error"


class ModelOutputError(OwnDraftError):
    code = "model_output_error"


class PreservationError(OwnDraftError):
    code = "preservation_error"


class GatewayError(OwnDraftError):
    code = "gateway_error"
