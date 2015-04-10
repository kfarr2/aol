from django.db import migrations, models

sql = """
DROP INDEX IF EXISTS lake_title_prefix_1;
DROP INDEX IF EXISTS lake_title_prefix_2;
CREATE INDEX lake_title_prefix_1 ON nhd USING BTREE(substring(lower(COALESCE(NULLIF(title, ''), gnis_name)) FROM 1 for 1));
CREATE INDEX lake_title_prefix_2 ON nhd USING BTREE(substring(lower(regexp_replace(COALESCE(NULLIF(title, ''), gnis_name), '^[lL]ake\s*', '')) FROM 1 for 1));
"""

class Migration(migrations.Migration):
    dependencies = [("lakes", "0001_initial")]

    operations = [
        migrations.RunSQL(sql)
    ]
