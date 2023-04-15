# Generated by Django 4.1.1 on 2023-04-15 13:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0010_alter_department_dep_name_alter_order_description_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='trusty',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='trusty', to='website.client'),
        ),
        migrations.AlterField(
            model_name='order',
            name='client',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='client', to='website.client'),
        ),
    ]
