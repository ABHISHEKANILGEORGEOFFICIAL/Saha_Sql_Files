from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Adminapp', '0003_subject_school_class_stream_and_more'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='course',
            unique_together=set(),
        ),
        migrations.RemoveField(
            model_name='course',
            name='college',
        ),
        migrations.AddField(
            model_name='course',
            name='department',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='courses', to='Adminapp.department'),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='course',
            unique_together={('department', 'course_name', 'year')},
        ),
    ]