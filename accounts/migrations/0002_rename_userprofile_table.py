from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE core_userprofile RENAME TO accounts_user_profile;",
            reverse_sql="ALTER TABLE accounts_userprofile RENAME TO core_userprofile;",
        ),
    ]