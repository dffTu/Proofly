ALTER TABLE graph_node ADD COLUMN title_en      VARCHAR(200);
ALTER TABLE graph_node ADD COLUMN title_ru      VARCHAR(200);
ALTER TABLE graph_node ADD COLUMN description_en TEXT;
ALTER TABLE graph_node ADD COLUMN description_ru TEXT;

-- Existing content is in Russian — move to _ru columns
UPDATE graph_node SET title_ru = title, description_ru = description;

ALTER TABLE graph_node DROP COLUMN title;
ALTER TABLE graph_node DROP COLUMN description;
