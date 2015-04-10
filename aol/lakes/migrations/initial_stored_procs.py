from django.db import migrations, models

sql = """
CREATE EXTENSION IF NOT EXISTS hstore;

ALTER TABLE nhd DROP COLUMN IF EXISTS changed_on;
ALTER TABLE nhd ADD COLUMN changed_on hstore NOT NULL DEFAULT ''::hstore;

CREATE OR REPLACE FUNCTION nhd_value_changed()
  RETURNS trigger AS
$BODY$
DECLARE
    new_hstore hstore;
    old_hstore hstore;
    changed_hstore hstore;
    rec RECORD;
BEGIN
    new_hstore = hstore(NEW);
    old_hstore = hstore(OLD);
    -- calculate which fields changed
    changed_hstore = new_hstore - old_hstore;

    -- loop over all the field names
    for rec in SELECT * FROM each(changed_hstore)
    loop
        -- we don't care about the changed_on field changing
        if  (rec.key = 'changed_on') then
            continue;
        end if;
        -- mark this field as being changed now
        NEW.changed_on = NEW.changed_on || hstore(rec.key, NOW()::varchar);
    end loop;

    return NEW;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;

DROP TRIGGER IF EXISTS nhd_value_changed ON nhd;
CREATE TRIGGER nhd_value_changed
  BEFORE UPDATE
  ON nhd
  FOR EACH ROW
  EXECUTE PROCEDURE nhd_value_changed();
"""

class Migration(migrations.Migration):
    dependencies = [("lakes", "initial_indexes")]

    operations = [
        migrations.RunSQL(sql)
    ]
