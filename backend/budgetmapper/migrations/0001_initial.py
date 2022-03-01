# Generated by Django 4.0.2 on 2022-02-28 15:16

import budgetmapper.models
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Blob',
            fields=[
                ('id', budgetmapper.models.PkField(blank=True, editable=False, max_length=22, primary_key=True, serialize=False)),
                ('name', budgetmapper.models.NameField(db_index=True, null=True)),
                ('created_at', budgetmapper.models.CurrentDateTimeField(default=django.utils.timezone.now, editable=False)),
                ('updated_at', budgetmapper.models.AutoUpdateCurrentDateTimeField(default=django.utils.timezone.now, editable=False)),
            ],
        ),
        migrations.CreateModel(
            name='BudgetBase',
            fields=[
                ('id', budgetmapper.models.PkField(blank=True, editable=False, max_length=22, primary_key=True, serialize=False)),
                ('name', budgetmapper.models.NameField(db_index=True, null=True)),
                ('slug', budgetmapper.models.JpSlugField(blank=True, null=True, unique=True)),
                ('subtitle', models.TextField(null=True)),
                ('created_at', budgetmapper.models.CurrentDateTimeField(default=django.utils.timezone.now, editable=False)),
                ('updated_at', budgetmapper.models.AutoUpdateCurrentDateTimeField(default=django.utils.timezone.now, editable=False)),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
        ),
        migrations.CreateModel(
            name='BudgetItemBase',
            fields=[
                ('id', budgetmapper.models.PkField(blank=True, editable=False, max_length=22, primary_key=True, serialize=False)),
                ('created_at', budgetmapper.models.CurrentDateTimeField(default=django.utils.timezone.now, editable=False)),
                ('updated_at', budgetmapper.models.AutoUpdateCurrentDateTimeField(default=django.utils.timezone.now, editable=False)),
                ('budget', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='budgetmapper.budgetbase')),
            ],
        ),
        migrations.CreateModel(
            name='ClassificationSystem',
            fields=[
                ('id', budgetmapper.models.PkField(blank=True, editable=False, max_length=22, primary_key=True, serialize=False)),
                ('name', budgetmapper.models.NameField(db_index=True, null=True)),
                ('slug', budgetmapper.models.JpSlugField(blank=True, null=True, unique=True)),
                ('level_names', budgetmapper.models.LevelNameListField(base_field=models.CharField(max_length=255), default=budgetmapper.models.get_default_level_name_list, null=True, size=None)),
                ('created_at', budgetmapper.models.CurrentDateTimeField(default=django.utils.timezone.now, editable=False)),
                ('updated_at', budgetmapper.models.AutoUpdateCurrentDateTimeField(default=django.utils.timezone.now, editable=False)),
            ],
        ),
        migrations.CreateModel(
            name='Government',
            fields=[
                ('id', budgetmapper.models.PkField(blank=True, editable=False, max_length=22, primary_key=True, serialize=False)),
                ('name', budgetmapper.models.NameField(db_index=True, null=True)),
                ('slug', budgetmapper.models.JpSlugField(blank=True, null=True, unique=True)),
                ('latitude', budgetmapper.models.LatitudeField(null=True, validators=[django.core.validators.MinValueValidator(-90.0), django.core.validators.MaxValueValidator(90.0)])),
                ('longitude', budgetmapper.models.LongitudeField(null=True, validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(180.0)])),
                ('primary_color_code', budgetmapper.models.ColorCodeField(max_length=8, null=True, validators=[django.core.validators.RegexValidator(code='invalid_colorcode_format', message='invalid_colorcode_format', regex='^#(?:[0-9a-fA-F]{3}){1,2}$')])),
                ('secondary_color_code', budgetmapper.models.ColorCodeField(max_length=8, null=True, validators=[django.core.validators.RegexValidator(code='invalid_colorcode_format', message='invalid_colorcode_format', regex='^#(?:[0-9a-fA-F]{3}){1,2}$')])),
                ('created_at', budgetmapper.models.CurrentDateTimeField(default=django.utils.timezone.now, editable=False)),
                ('updated_at', budgetmapper.models.AutoUpdateCurrentDateTimeField(default=django.utils.timezone.now, editable=False)),
            ],
        ),
        migrations.CreateModel(
            name='IconImage',
            fields=[
                ('id', budgetmapper.models.PkField(blank=True, editable=False, max_length=22, primary_key=True, serialize=False)),
                ('name', budgetmapper.models.NameField(db_index=True, null=True)),
                ('slug', budgetmapper.models.JpSlugField(blank=True, null=True, unique=True)),
                ('image_type', budgetmapper.models.ImageTypeField(choices=[('svg+xml', 'svg+xml'), ('jpeg', 'jpeg'), ('png', 'png'), ('gif', 'gif')], max_length=8)),
                ('body', models.BinaryField()),
                ('created_at', budgetmapper.models.CurrentDateTimeField(default=django.utils.timezone.now, editable=False)),
                ('updated_at', budgetmapper.models.AutoUpdateCurrentDateTimeField(default=django.utils.timezone.now, editable=False)),
            ],
        ),
        migrations.CreateModel(
            name='AtomicBudgetItem',
            fields=[
                ('budgetitembase_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='budgetmapper.budgetitembase')),
                ('value', budgetmapper.models.BudgetAmountField()),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('budgetmapper.budgetitembase',),
        ),
        migrations.CreateModel(
            name='WdmmgTreeCache',
            fields=[
                ('id', budgetmapper.models.PkField(blank=True, editable=False, max_length=22, primary_key=True, serialize=False)),
                ('created_at', budgetmapper.models.CurrentDateTimeField(default=django.utils.timezone.now, editable=False)),
                ('updated_at', budgetmapper.models.AutoUpdateCurrentDateTimeField(default=django.utils.timezone.now, editable=False)),
                ('blob', models.ForeignKey(db_index=False, on_delete=django.db.models.deletion.CASCADE, to='budgetmapper.blob')),
                ('budget', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='budgetmapper.budgetbase')),
            ],
        ),
        migrations.CreateModel(
            name='DefaultBudget',
            fields=[
                ('id', budgetmapper.models.PkField(blank=True, editable=False, max_length=22, primary_key=True, serialize=False)),
                ('created_at', budgetmapper.models.CurrentDateTimeField(default=django.utils.timezone.now, editable=False)),
                ('updated_at', budgetmapper.models.AutoUpdateCurrentDateTimeField(default=django.utils.timezone.now, editable=False)),
                ('budget', models.OneToOneField(db_index=False, on_delete=django.db.models.deletion.CASCADE, to='budgetmapper.budgetbase')),
                ('government', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='budgetmapper.government')),
            ],
        ),
        migrations.CreateModel(
            name='Classification',
            fields=[
                ('id', budgetmapper.models.PkField(blank=True, editable=False, max_length=22, primary_key=True, serialize=False)),
                ('name', budgetmapper.models.NameField(db_index=True, null=True)),
                ('code', models.CharField(db_index=True, max_length=64, null=True)),
                ('item_order', budgetmapper.models.ItemOrderField(db_index=True, null=True)),
                ('created_at', budgetmapper.models.CurrentDateTimeField(default=django.utils.timezone.now, editable=False)),
                ('updated_at', budgetmapper.models.AutoUpdateCurrentDateTimeField(default=django.utils.timezone.now, editable=False)),
                ('classification_system', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='budgetmapper.classificationsystem')),
                ('icon', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='budgetmapper.iconimage')),
                ('parent', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='budgetmapper.classification')),
            ],
            options={
                'unique_together': {('classification_system', 'item_order')},
            },
        ),
        migrations.AddField(
            model_name='budgetitembase',
            name='classification',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='budgetmapper.classification'),
        ),
        migrations.AddField(
            model_name='budgetitembase',
            name='polymorphic_ctype',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='polymorphic_%(app_label)s.%(class)s_set+', to='contenttypes.contenttype'),
        ),
        migrations.AddField(
            model_name='budgetbase',
            name='classification_system',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='budgetmapper.classificationsystem'),
        ),
        migrations.AddField(
            model_name='budgetbase',
            name='polymorphic_ctype',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='polymorphic_%(app_label)s.%(class)s_set+', to='contenttypes.contenttype'),
        ),
        migrations.CreateModel(
            name='MappedBudgetItem',
            fields=[
                ('budgetitembase_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='budgetmapper.budgetitembase')),
                ('source_classifications', models.ManyToManyField(related_name='mapping_classifications', to='budgetmapper.Classification')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('budgetmapper.budgetitembase',),
        ),
        migrations.CreateModel(
            name='MappedBudget',
            fields=[
                ('budgetbase_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='budgetmapper.budgetbase')),
                ('source_budget', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mapped_budget', to='budgetmapper.budgetbase')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('budgetmapper.budgetbase',),
        ),
        migrations.AlterUniqueTogether(
            name='budgetitembase',
            unique_together={('budget', 'classification')},
        ),
        migrations.CreateModel(
            name='BlobChunk',
            fields=[
                ('id', budgetmapper.models.PkField(blank=True, editable=False, max_length=22, primary_key=True, serialize=False)),
                ('index', models.PositiveIntegerField()),
                ('body', models.BinaryField()),
                ('blob', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='budgetmapper.blob')),
            ],
            options={
                'unique_together': {('blob', 'index')},
            },
        ),
        migrations.CreateModel(
            name='BasicBudget',
            fields=[
                ('budgetbase_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='budgetmapper.budgetbase')),
                ('year_value', models.IntegerField(db_index=True)),
                ('government_value', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='budgetmapper.government')),
            ],
            bases=('budgetmapper.budgetbase',),
        ),
        migrations.AddIndex(
            model_name='basicbudget',
            index=models.Index(fields=['government_value', 'year_value'], name='budgetmappe_governm_3536ec_idx'),
        ),
    ]