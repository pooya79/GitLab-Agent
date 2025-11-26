from .add_docs import AddDocsCommand, AddDocsDocumentation, AddDocsInput, AddDocsOutput
from .command_interface import CommandInterface
from .help import HelpCommand
from .describe import (
    DescribeCommand,
    DescribeInput,
    FileDescription,
    MRDescriptionOutput,
    MRType,
    RelatedIssue as DescribeRelatedIssue,
)
from .review import (
    IssueCompliance,
    KeyIssuesComponentLink,
    MRReviewOutput,
    ReviewBody,
    ReviewCommand,
    ReviewInput,
    TodoSection,
)
from .suggest import (
    CodeSuggestion,
    CodeSuggestionFeedback,
    MRCodeSuggestionsFeedbackOutput,
    MRCodeSuggestionsOutput,
    SuggestCommand,
    SuggestFeedbackCommand,
    SuggestFeedbackInput,
    SuggestInput,
)


class CommandParseError(Exception):
    pass


__all__ = [
    "CommandInterface",
    "HelpCommand",
    "AddDocsCommand",
    "AddDocsDocumentation",
    "AddDocsInput",
    "AddDocsOutput",
    "MRType",
    "DescribeRelatedIssue",
    "DescribeCommand",
    "DescribeInput",
    "FileDescription",
    "MRDescriptionOutput",
    "ReviewCommand",
    "ReviewInput",
    "ReviewBody",
    "MRReviewOutput",
    "IssueCompliance",
    "KeyIssuesComponentLink",
    "TodoSection",
    "CodeSuggestion",
    "CodeSuggestionFeedback",
    "MRCodeSuggestionsOutput",
    "MRCodeSuggestionsFeedbackOutput",
    "SuggestCommand",
    "SuggestFeedbackCommand",
    "SuggestFeedbackInput",
    "SuggestInput",
]
