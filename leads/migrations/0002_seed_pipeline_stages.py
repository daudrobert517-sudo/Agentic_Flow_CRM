from django.db import migrations


def create_stages(apps, schema_editor):
    PipelineStage = apps.get_model('leads', 'PipelineStage')
    stages = [
        ('New', 0, '#3b82f6'),
        ('Contacted', 1, '#8b5cf6'),
        ('Qualified', 2, '#f59e0b'),
        ('Proposal', 3, '#ec4899'),
        ('Won', 4, '#10b981'),
        ('Lost', 5, '#ef4444'),
    ]
    for name, order, color in stages:
        PipelineStage.objects.create(name=name, order=order, color=color)


def remove_stages(apps, schema_editor):
    PipelineStage = apps.get_model('leads', 'PipelineStage')
    PipelineStage.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_stages, remove_stages),
    ]