"""Indexes for catalogue filters and reverse relationship traversal."""

# Primary/unique keys already cover forward links and source/artifact identities.
INDEXES = {
    "quantities_event": ("quantities", ("event_id", "id")),
    "quantities_series": ("quantities", ("series_id", "id")),
    "quantities_page": ("quantities", ("source_id", "printed_page", "id")),
    "quantities_role": ("quantities", ("role", "id")),
    "interpretations_type_subject": (
        "interpretations",
        ("quantity", "subject", "quantity_id", "version"),
    ),
    "groups_clock": ("groups", ("clock_quantity_id", "id")),
    "groups_epoch": ("groups", ("epoch_quantity_id", "id")),
    "contexts_source": ("contexts", ("source_id", "context_id", "scope_id")),
    "quantity_contexts_reverse": ("quantity_contexts", ("context_id", "scope_id", "id")),
    "group_contexts_reverse": ("group_contexts", ("context_id", "scope_id", "id")),
    "source_loci_page": ("source_loci", ("source_id", "printed_page", "id")),
    "locus_quantities_reverse": ("locus_quantities", ("quantity_id", "locus_id")),
    "locus_contexts_reverse": ("locus_contexts", ("context_id", "scope_id", "locus_id")),
    "quantity_dates_reverse": ("quantity_dates", ("date_id", "quantity_id")),
    "group_dates_reverse": ("group_dates", ("date_id", "group_id")),
    "series_quantities_reverse": ("series_quantities", ("quantity_id", "series_id")),
    "derivations_output": ("derivations", ("output_quantity_id", "id")),
    "derivation_inputs_quantity": ("derivation_inputs", ("quantity_id", "derivation_id")),
    "control_links_quantity": ("control_links", ("quantity_id", "control_id")),
    "quantity_links_reverse": ("quantity_links", ("to_id", "kind", "from_id")),
}


def create_indexes(db):
    for name, (table, columns) in INDEXES.items():
        db.execute(f"CREATE INDEX IF NOT EXISTS {name} ON {table} ({','.join(columns)})")


def validate_indexes(db):
    for name, (table, columns) in INDEXES.items():
        found = db.execute(
            "SELECT tbl_name FROM sqlite_master WHERE type='index' AND name=?", (name,)
        ).fetchone()
        actual = tuple(r[2] for r in db.execute(f"PRAGMA index_info({name})"))
        if not found or found[0] != table or actual != columns:
            raise ValueError("Missing or incompatible catalogue index: " + name)
