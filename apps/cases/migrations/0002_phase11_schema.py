"""Phase 11 schema migration.

Replaces the placeholder clinical fields (blood_pressure, respiratory_rate,
temperature, urea, ph, wbc_count, confusion) with the real model inputs
(bun, hr, sys_bp, rr, temp_fahrenheit, gcs_total).

Replaces the placeholder AI output fields (severity_score, risk_class,
confidence_score) with the real model outputs (diag_probability,
severity_probability, has_pneumonia, is_severe).

Adds FAILED to the status choices.

All existing test data is deleted first — the schema change is fundamental
and incompatible with old rows.
"""
import django.core.validators
from django.db import migrations, models


def delete_old_data(apps, schema_editor):
    PatientCase = apps.get_model("cases", "PatientCase")
    ClinicalData = apps.get_model("cases", "ClinicalData")
    PatientCase.objects.all().delete()
    ClinicalData.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("cases", "0001_initial"),
    ]

    operations = [
        # Clear incompatible test data before altering the schema
        migrations.RunPython(delete_old_data, migrations.RunPython.noop),

        # ── ClinicalData: remove old placeholder fields ──────────────────────
        migrations.RemoveField(model_name="ClinicalData", name="blood_pressure"),
        migrations.RemoveField(model_name="ClinicalData", name="respiratory_rate"),
        migrations.RemoveField(model_name="ClinicalData", name="temperature"),
        migrations.RemoveField(model_name="ClinicalData", name="urea"),
        migrations.RemoveField(model_name="ClinicalData", name="ph"),
        migrations.RemoveField(model_name="ClinicalData", name="wbc_count"),
        migrations.RemoveField(model_name="ClinicalData", name="confusion"),

        # ── ClinicalData: add real model input fields ────────────────────────
        migrations.AddField(
            model_name="ClinicalData",
            name="bun",
            field=models.FloatField(default=10.0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="ClinicalData",
            name="hr",
            field=models.PositiveIntegerField(default=70),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="ClinicalData",
            name="sys_bp",
            field=models.PositiveIntegerField(default=120),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="ClinicalData",
            name="rr",
            field=models.PositiveIntegerField(default=16),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="ClinicalData",
            name="temp_fahrenheit",
            field=models.FloatField(default=98.6),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="ClinicalData",
            name="gcs_total",
            field=models.PositiveIntegerField(
                default=15,
                validators=[
                    django.core.validators.MinValueValidator(3),
                    django.core.validators.MaxValueValidator(15),
                ],
            ),
            preserve_default=False,
        ),

        # ── PatientCase: remove old AI output fields ─────────────────────────
        migrations.RemoveField(model_name="PatientCase", name="severity_score"),
        migrations.RemoveField(model_name="PatientCase", name="risk_class"),
        migrations.RemoveField(model_name="PatientCase", name="confidence_score"),

        # ── PatientCase: add new AI output fields ────────────────────────────
        migrations.AddField(
            model_name="PatientCase",
            name="diag_probability",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="PatientCase",
            name="severity_probability",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="PatientCase",
            name="has_pneumonia",
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="PatientCase",
            name="is_severe",
            field=models.BooleanField(blank=True, null=True),
        ),

        # ── PatientCase: add FAILED to status choices ─────────────────────────
        migrations.AlterField(
            model_name="PatientCase",
            name="status",
            field=models.CharField(
                choices=[
                    ("PENDING", "Pending"),
                    ("DONE", "Done"),
                    ("FAILED", "Failed"),
                ],
                default="PENDING",
                max_length=10,
            ),
        ),
    ]
