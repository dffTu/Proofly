CREATE TABLE IF NOT EXISTS graph_node (
    id          BIGSERIAL    PRIMARY KEY,
    slug        VARCHAR(100) NOT NULL UNIQUE,
    title       VARCHAR(200) NOT NULL,
    node_type   VARCHAR(10)  NOT NULL CHECK (node_type IN ('axiom', 'theorem')),
    level       INTEGER      NOT NULL CHECK (level >= 0),
    description TEXT         NOT NULL
);

CREATE TABLE IF NOT EXISTS graph_edge (
    id           BIGSERIAL PRIMARY KEY,
    from_node_id BIGINT    NOT NULL REFERENCES graph_node(id) ON DELETE CASCADE,
    to_node_id   BIGINT    NOT NULL REFERENCES graph_node(id) ON DELETE CASCADE,
    UNIQUE (from_node_id, to_node_id)
);
