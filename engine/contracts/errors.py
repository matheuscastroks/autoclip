class PipelineError(RuntimeError):
    def __init__(self, code: str, stage: str, message: str, retryable: bool = False):
        self.code, self.stage, self.retryable = code, stage, retryable
        super().__init__(message)

    def as_dict(self):
        return {'code': self.code, 'stage': self.stage, 'message': str(self), 'retryable': self.retryable}
