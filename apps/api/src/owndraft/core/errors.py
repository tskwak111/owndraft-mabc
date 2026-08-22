class OwnDraftError(Exception):
    code = "owndraft_error"


class ContractError(OwnDraftError):
    code = "contract_error"


class ModelOutputError(OwnDraftError):
    code = "model_output_error"


class PreservationError(OwnDraftError):
    code = "preservation_error"
