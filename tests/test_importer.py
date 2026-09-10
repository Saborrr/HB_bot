from hb_bot.importer import parse_csv


def test_csv_parser_accepts_dates_with_and_without_year():
    plan = parse_csv(
        "external_id,full_name,birth_date\ne-1,Иванов Иван,15.09.1990\ne-2,Петрова Анна,03.12\n"
    )

    assert not plan.errors
    assert [record.external_id for record in plan.records] == ["e-1", "e-2"]
    assert plan.records[1].birthday.year is None


def test_csv_parser_reports_duplicate_and_invalid_rows_without_partial_silence():
    plan = parse_csv("external_id,full_name,birth_date\ne-1,Иванов Иван,31.02\ne-1,,01.01.2000\n")

    assert plan.records == []
    assert len(plan.errors) == 2
    assert "строка 2" in plan.errors[0]
    assert "строка 3" in plan.errors[1]


def test_csv_parser_requires_exact_headers():
    plan = parse_csv("name,date\nИванов,01.01\n")
    assert plan.records == []
    assert plan.errors == ["Ожидаются столбцы: external_id, full_name, birth_date"]


def test_csv_parser_rejects_empty_dataset():
    plan = parse_csv("external_id,full_name,birth_date\n")
    assert plan.records == []
    assert plan.errors == ["CSV не содержит записей"]


def test_csv_parser_rejects_values_longer_than_database_columns():
    plan = parse_csv(f"external_id,full_name,birth_date\n{'x' * 129},{'И' * 256},01.01\n")

    assert plan.records == []
    assert len(plan.errors) == 1
    assert "external_id длиннее 128" in plan.errors[0]
    assert "full_name длиннее 255" in plan.errors[0]


def test_csv_parser_rejects_rows_with_extra_columns():
    plan = parse_csv("external_id,full_name,birth_date\ne-1,Name,01.01,EXTRA\n")

    assert plan.records == []
    assert "лишн" in plan.errors[0]
