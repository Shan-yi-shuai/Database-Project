import ast
from match.issue import *

class LocationSyntaxRecorder(ast.NodeVisitor):
    def __init__(self, location: RawIssueLocation) -> None:
        super().__init__()
        self.location = location
        self.records = []
        self.include_records = []
    
    def visit(self, node: ast.AST) -> None:
        if (len(node._attributes) == 4):
            if (self.is_before_location(node)):
                self.records.append(type(node).__name__)
                return
            elif (self.is_include_location(node)):
                self.records.append(type(node).__name__)
                self.include_records.append(type(node).__name__)
                if ("name" in node._fields):
                    self.records.append(node.name)
                    self.include_records.append(node.name)
            else:
                return
        super().visit(node)
    
    def is_before_location(self, node: ast.AST) -> bool:
        # an ast.AST node
        # either have no attrs or have 4 which refer code postion
        # this judgment must accept a node with 4 attrs
        assert(len(node._attributes) == 4)
        return node.end_lineno < self.location.start_line or (node.end_lineno == self.location.start_line and node.end_col_offset < self.location.start_offset)
    
    def is_include_location(self, node: ast.AST) -> bool:
        # an ast.AST node
        # either have no attrs or have 4 which refer code postion
        # this judgment must accept a node with 4 attrs
        assert(len(node._attributes) == 4)
        return (node.lineno < self.location.start_line or (node.lineno == self.location.start_line and node.col_offset <= self.location.start_offset)) and (node.end_lineno > self.location.end_line or (node.end_lineno == self.location.end_line and node.end_col_offset >= self.location.end_offset))