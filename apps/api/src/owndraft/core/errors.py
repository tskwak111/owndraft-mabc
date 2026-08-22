class OwnDraftError(Exception):
    """Base error with a stable machine-readable code and Korean detail."""

    code: str = "owndraft_error"

    def __init__(self, code: str | None = None, detail: str = "") -> None:
        if code is not None:
            self.code = code
        self.detail = detail
        super().__init__(f"{self.code}: {detail}" if detail else self.code)


class ContractError(OwnDraftError):
    code = "contract_error"


class ModelOutputError(OwnDraftError):
    code = "model_output_error"


class PreservationError(OwnDraftError):
    code = "preservation_error"


class GatewayError(OwnDraftError):
    code = "gateway_error"
