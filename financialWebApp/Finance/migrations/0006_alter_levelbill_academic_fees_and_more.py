# Generated by Django 4.0.8 on 2024-04-03 19:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Finance', '0005_session_levelbill_academic_session_payment_session'),
    ]

    operations = [
        migrations.AlterField(
            model_name='levelbill',
            name='academic_fees',
            field=models.FloatField(null=True),
        ),
        migrations.AlterField(
            model_name='levelbill',
            name='exams_fees',
            field=models.FloatField(null=True),
        ),
        migrations.AlterField(
            model_name='levelbill',
            name='student_fees',
            field=models.FloatField(null=True),
        ),
    ]
