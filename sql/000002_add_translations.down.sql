ALTER TABLE graph_node ADD COLUMN title       VARCHAR(200);
ALTER TABLE graph_node ADD COLUMN description TEXT;

UPDATE graph_node SET title = COALESCE(title_ru, title_en), description = COALESCE(description_ru, description_en);

ALTER TABLE graph_node DROP COLUMN title_en;
ALTER TABLE graph_node DROP COLUMN title_ru;
ALTER TABLE graph_node DROP COLUMN description_en;
ALTER TABLE graph_node DROP COLUMN description_ru;
