CREATE TABLE tasks (
    artifact_hashstring text,
    document_key text,
    batch_id integer,
    batch_order integer,
    host text,
    pid integer,
    exit_status integer,
    complete boolean default 'f'
);

