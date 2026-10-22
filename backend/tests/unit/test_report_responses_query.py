"""The report-response query must build and compile without FK inference."""

from uuid import uuid4

from sqlalchemy.dialects import postgresql

from app.api.v1.modules.civic_action.repository import (
    institution_responses_statement,
)


def test_institution_responses_statement_joins_through_report_links() -> None:
    statement = institution_responses_statement(uuid4())

    sql = str(statement.compile(dialect=postgresql.dialect()))

    assert "FROM institution_responses JOIN report_institution_links ON" in sql
    assert (
        "institution_responses.report_institution_link_id = "
        "report_institution_links.id" in sql
    )
    assert "report_institution_links.institution_id = institutions.id" in sql
