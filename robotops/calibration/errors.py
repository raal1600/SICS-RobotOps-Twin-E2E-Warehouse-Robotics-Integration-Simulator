"""Structured failures: an unsuccessful calculation never returns a fallback target."""


class CalibrationError(ValueError):
    def __init__(
        self, code: str, detail: str = "", *, calculation: dict[str, object] | None = None
    ) -> None:
        self.code = code
        self.detail = detail
        self.calculation = calculation
        super().__init__(code + (": " + detail if detail else ""))

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "detail": self.detail}
