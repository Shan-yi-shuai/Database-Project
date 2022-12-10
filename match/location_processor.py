from match.ast_recorder import *

class LocationProcessor:
    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        code = open(file_path, encoding="utf-8").read()
        self.code_lines = code.splitlines()
        self.ast_root = ast.parse(code)
    
    def process_code(self, location: RawIssueLocation) -> str:
        if (location.start_line == location.end_line):
            code = self.code_lines[location.start_line - 1][location.start_offset : location.end_offset]
        else:
            code = self.code_lines[location.start_line - 1][location.start_offset :] + "\n"
            if (location.start_line < location.end_line - 1):
                code += "\n".join(self.code_lines[location.start_line : location.end_line - 1]) + "\n"
            code += self.code_lines[location.end_line - 1][0 : location.end_offset]
        return code
    
    def process_record(self, location: RawIssueLocation) -> tuple[list[str], list[str]]:
        tracker = LocationSyntaxRecorder(location)
        tracker.visit(self.ast_root)
        return (tracker.include_records, tracker.records)
    
    def process(self, location: RawIssueLocation):
        return IssueLocation(location, self.process_code(location), *self.process_record(location))

