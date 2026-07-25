from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('Adminapp', '0001_initial'),
        ('Guestapp', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('content', models.TextField(blank=True)),
                ('post_type', models.CharField(choices=[('post', 'Post'), ('photo', 'Photo'), ('note', 'Note')], max_length=10)),
                ('image', models.ImageField(blank=True, null=True, upload_to='posts/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('likes', models.ManyToManyField(blank=True, related_name='liked_posts', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Reply',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='replies', to='Teacherapp.post')),
            ],
        ),
        migrations.CreateModel(
            name='Tuition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('max_students', models.PositiveIntegerField(blank=True, null=True)),
                ('days', models.JSONField(blank=True, default=list)),
                ('start_time', models.TimeField(blank=True, null=True)),
                ('end_time', models.TimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('class_level', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='Adminapp.classes')),
                ('college', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='Adminapp.college')),
                ('course', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='Adminapp.course')),
                ('school', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='Adminapp.school')),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Adminapp.subject')),
                ('teacher', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tuitions', to='Guestapp.classteacher')),
            ],
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('task_type', models.CharField(choices=[('homework', 'Homework'), ('assignment', 'Assignment'), ('test', 'Test'), ('seminar', 'Seminar')], max_length=20)),
                ('attachment', models.FileField(blank=True, null=True, upload_to='tasks/')),
                ('due_date', models.DateField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('tuition', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tasks', to='Teacherapp.tuition')),
            ],
        ),
    ]
