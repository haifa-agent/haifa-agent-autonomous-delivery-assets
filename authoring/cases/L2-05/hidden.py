CREATION_ORDER = [f"rec-{(index * 37) % 97 + 1:03d}" for index in range(60)]


def _ids(records):
    return [record["id"] for record in records]


@check("functional.pageSizeApplied")
def page_size_applied():
    from listing import list_records

    return (
        len(list_records(page_size=5)) == 5
        and len(list_records(1)) == 1
        and len(list_records(page_size=100)) == 60
        and len(list_records(page_size=37)) == 37
    )


@check("functional.defaultStaysTwenty")
def default_twenty():
    from listing import list_records

    return len(list_records()) == 20


@check("boundary.rangeValidation")
def range_validation():
    from listing import list_records

    for invalid in (0, 101, -1, 1000):
        try:
            list_records(page_size=invalid)
        except ValueError:
            continue
        return False, f"page_size={invalid} was accepted"
    return True


@check("functional.pagesFollowDefaultOrder")
def pages_follow_default_order():
    from listing import list_records

    page = _ids(list_records(page_size=7))
    everything = _ids(list_records(page_size=100))
    return page == CREATION_ORDER[:7] and everything == CREATION_ORDER, f"page of 7 is {page}"


@check("regression.defaultOrderUnchanged")
def default_order():
    from listing import list_records

    default = _ids(list_records())
    return default == CREATION_ORDER[:20], f"default listing starts with {default[:4]}"


@check("regression.recordShapeUnchanged")
def record_shape():
    from listing import list_records

    records = list_records()
    return isinstance(records, list) and all(isinstance(record, dict) and set(record) == {"id", "name"} for record in records)


@check("regression.resultsAreCopies")
def results_are_copies():
    from listing import list_records
    from repository import all_records

    first = list_records()
    first[0]["name"] = "tampered"
    first.clear()
    return all_records()[0]["name"] != "tampered" and list_records()[0]["name"] != "tampered"


@check("regression.dashboardUnchanged")
def dashboard():
    from dashboard import dashboard_rows

    expected = [f"{record_id}: Record {int(record_id[4:])}" for record_id in CREATION_ORDER[:20]]
    return dashboard_rows() == expected
