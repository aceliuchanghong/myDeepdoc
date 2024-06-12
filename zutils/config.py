# sqlite
LOG_LEVEL = "ERROR"
db_path = "font_labels.db"
segment_length = 3500

create_table_sql = """
CREATE TABLE IF NOT EXISTS font_label_info
(pkl_path TEXT,nums TEXT, remark TEXT)
"""
table_select_nums_count_sql = """
select count(*) from font_label_info where pkl_path = ?
"""
table_select_nums_sql = """
select nums from font_label_info where pkl_path = ?
"""
table_count_sql = """
select count(*) from font_label_info
"""
table_all_sql = """
select * from font_label_info
"""
table_add_sql = """
INSERT INTO font_label_info (pkl_path, nums, remark)
VALUES (?, ?, ?)
"""
table_del_url_sql = """
delete from font_label_info where pkl_path = ?
"""
table_truncate_sql = """
DELETE FROM font_label_info
"""
