INSERT INTO my_table
    VALUES (%(filename)s)
ON CONFLICT(table_val)
DO UPDATE
    SET table_val='my_new_val';
