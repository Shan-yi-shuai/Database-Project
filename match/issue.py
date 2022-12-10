class RawIssueLocation:
    def __init__(self, id: int, file_path: str, start_line: int, end_line: int, start_offset: int, end_offset: int) -> None:
        self.id = id
        self.file_path = file_path
        self.start_line = start_line
        self.end_line = end_line
        self.start_offset = start_offset
        self.end_offset = end_offset

class IssueLocation(RawIssueLocation):
    def __init__(self, id: int, file_path: str, start_line: int, end_line: int, start_offset: int, end_offset: int, code: str, records: list[str], include_records: list[str]) -> None:
        super().__init__(id, file_path, start_line, end_line, start_offset, end_offset)
        self.code = code
        self.records = records
        self.include_records = include_records
    
    def __init__(self, rawLocation: RawIssueLocation, code: str, records: list[str], include_records: list[str]) -> None:
        super().__init__(**rawLocation.__dict__)
        self.code = code
        self.records = records
        self.include_records = include_records


class IssueInstance:
    def __init__(self, rule: str, locations: list[IssueLocation]) -> None:
        self.rule = rule
        self.locations = locations
