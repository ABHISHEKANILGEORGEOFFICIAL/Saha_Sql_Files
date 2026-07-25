from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('Adminapp', '0004_course_department'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='subject',
            unique_together={('type', 'department', 'school_class', 'stream', 'subject_name')},
        ),
    ]
