from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Adminapp', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='subject',
            name='school',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='subjects', to='Adminapp.school'),
        ),
        migrations.AlterUniqueTogether(
            name='subject',
            unique_together={('type', 'department', 'school', 'subject_name')},
        ),
    ]