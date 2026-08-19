import bloomerp.model_fields.user_field
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bloomerp_modules', '0008_account_allow_manual_posting_account_currency_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='account',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='account',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='account',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='account',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='account',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='account',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='accountbalance',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='accountbalance',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='accountbalance',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='accountbalance',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='accountbalance',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='accountbalance',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='activity',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='activity',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='activity',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='activity',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='activity',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='activity',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='application',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='application',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='application',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='application',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='application',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='application',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='attendancerecord',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='attendancerecord',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='attendancerecord',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='attendancerecord',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='attendancerecord',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='attendancerecord',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='bankaccount',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='bankaccount',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='bankaccount',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='bankaccount',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='bankaccount',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='bankaccount',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='billofmaterial',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='billofmaterial',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='billofmaterial',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='billofmaterial',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='billofmaterial',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='billofmaterial',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='billofmaterialline',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='billofmaterialline',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='billofmaterialline',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='billofmaterialline',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='billofmaterialline',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='billofmaterialline',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='budget',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='budget',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='budget',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='budget',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='budget',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='budget',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='candidate',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='candidate',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='candidate',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='candidate',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='candidate',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='candidate',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='contact',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='contact',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='contact',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='contact',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='contact',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='contact',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='costcenter',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='costcenter',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='costcenter',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='costcenter',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='costcenter',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='costcenter',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='costrate',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='costrate',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='costrate',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='costrate',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='costrate',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='costrate',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='crmaccount',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='crmaccount',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='crmaccount',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='crmaccount',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='crmaccount',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='crmaccount',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='customer',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='customer',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='customer',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='customer',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='customer',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='customer',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='customerinvoice',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='customerinvoice',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='customerinvoice',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='customerinvoice',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='customerinvoice',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='customerinvoice',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='customerinvoiceline',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='customerinvoiceline',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='customerinvoiceline',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='customerinvoiceline',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='customerinvoiceline',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='customerinvoiceline',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='customerreceipt',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='customerreceipt',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='customerreceipt',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='customerreceipt',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='customerreceipt',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='customerreceipt',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='department',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='department',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='department',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='department',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='department',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='department',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='employee',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='employee',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='employee',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='employee',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='employee',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='employee',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='employeecontract',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='employeecontract',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='employeecontract',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='employeecontract',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='employeecontract',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='employeecontract',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='equipment',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='equipment',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='equipment',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='equipment',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='equipment',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='equipment',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='exitinterview',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='exitinterview',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='exitinterview',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='exitinterview',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='exitinterview',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='exitinterview',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='exitreason',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='exitreason',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='exitreason',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='exitreason',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='exitreason',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='exitreason',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='fiscalperiod',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='fiscalperiod',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='fiscalperiod',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='fiscalperiod',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='fiscalperiod',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='fiscalperiod',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='gltransaction',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='gltransaction',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='gltransaction',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='gltransaction',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='gltransaction',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='gltransaction',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='goal',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='goal',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='goal',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='goal',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='goal',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='goal',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='goalprogress',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='goalprogress',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='goalprogress',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='goalprogress',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='goalprogress',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='goalprogress',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='hiringdecision',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='hiringdecision',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='hiringdecision',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='hiringdecision',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='hiringdecision',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='hiringdecision',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='hrcostcenter',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='hrcostcenter',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='hrcostcenter',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='hrcostcenter',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='hrcostcenter',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='hrcostcenter',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='interview',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='interview',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='interview',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='interview',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='interview',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='interview',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='interviewfeedback',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='interviewfeedback',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='interviewfeedback',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='interviewfeedback',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='interviewfeedback',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='interviewfeedback',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='jobopening',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='jobopening',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='jobopening',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='jobopening',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='jobopening',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='jobopening',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='jobtitle',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='jobtitle',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='jobtitle',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='jobtitle',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='jobtitle',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='jobtitle',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='journal',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='journal',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='journal',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='journal',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='journal',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='journal',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='journalentry',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='journalentry',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='journalentry',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='journalentry',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='journalentry',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='journalentry',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='journalentryline',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='journalentryline',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='journalentryline',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='journalentryline',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='journalentryline',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='journalentryline',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='lead',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='lead',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='lead',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='lead',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='lead',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='lead',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='leavebalance',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='leavebalance',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='leavebalance',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='leavebalance',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='leavebalance',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='leavebalance',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='leavepolicy',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='leavepolicy',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='leavepolicy',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='leavepolicy',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='leavepolicy',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='leavepolicy',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='leaverequest',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='leaverequest',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='leaverequest',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='leaverequest',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='leaverequest',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='leaverequest',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='leavetype',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='leavetype',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='leavetype',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='leavetype',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='leavetype',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='leavetype',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='location',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='location',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='location',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='location',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='location',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='location',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='maintenanceplan',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='maintenanceplan',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='maintenanceplan',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='maintenanceplan',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='maintenanceplan',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='maintenanceplan',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='maintenancerequest',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='maintenancerequest',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='maintenancerequest',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='maintenancerequest',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='maintenancerequest',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='maintenancerequest',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='maintenanceworkorder',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='maintenanceworkorder',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='maintenanceworkorder',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='maintenanceworkorder',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='maintenanceworkorder',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='maintenanceworkorder',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='manufacturingorder',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='manufacturingorder',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='manufacturingorder',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='manufacturingorder',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='manufacturingorder',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='manufacturingorder',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='manufacturingordercomponent',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='manufacturingordercomponent',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='manufacturingordercomponent',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='manufacturingordercomponent',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='manufacturingordercomponent',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='manufacturingordercomponent',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='manufacturingorderoperation',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='manufacturingorderoperation',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='manufacturingorderoperation',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='manufacturingorderoperation',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='manufacturingorderoperation',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='manufacturingorderoperation',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='masterproductionschedule',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='masterproductionschedule',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='masterproductionschedule',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='masterproductionschedule',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='masterproductionschedule',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='masterproductionschedule',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='mrprun',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='mrprun',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='mrprun',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='mrprun',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='mrprun',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='mrprun',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='nonconformancereport',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='nonconformancereport',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='nonconformancereport',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='nonconformancereport',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='nonconformancereport',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='nonconformancereport',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='offboardingprocess',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='offboardingprocess',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='offboardingprocess',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='offboardingprocess',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='offboardingprocess',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='offboardingprocess',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='offer',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='offer',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='offer',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='offer',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='offer',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='offer',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='offerapproval',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='offerapproval',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='offerapproval',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='offerapproval',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='offerapproval',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='offerapproval',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='officelocation',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='officelocation',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='officelocation',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='officelocation',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='officelocation',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='officelocation',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='onboardingprocess',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='onboardingprocess',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='onboardingprocess',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='onboardingprocess',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='onboardingprocess',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='onboardingprocess',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='onboardingtask',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='onboardingtask',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='onboardingtask',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='onboardingtask',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='onboardingtask',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='onboardingtask',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='onboardingtaskassignment',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='onboardingtaskassignment',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='onboardingtaskassignment',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='onboardingtaskassignment',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='onboardingtaskassignment',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='onboardingtaskassignment',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='operation',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='operation',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='operation',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='operation',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='operation',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='operation',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='opportunity',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='opportunity',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='opportunity',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='opportunity',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='opportunity',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='opportunity',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='opportunitystage',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='opportunitystage',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='opportunitystage',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='opportunitystage',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='opportunitystage',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='opportunitystage',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='overtimerule',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='overtimerule',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='overtimerule',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='overtimerule',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='overtimerule',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='overtimerule',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='peerfeedback',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='peerfeedback',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='peerfeedback',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='peerfeedback',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='peerfeedback',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='peerfeedback',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='performancecycle',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='performancecycle',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='performancecycle',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='performancecycle',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='performancecycle',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='performancecycle',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='performancereview',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='performancereview',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='performancereview',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='performancereview',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='performancereview',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='performancereview',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='person',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='person',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='person',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='person',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='person',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='person',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='plannedorder',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='plannedorder',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='plannedorder',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='plannedorder',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='plannedorder',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='plannedorder',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='product',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='product',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='product',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='product',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='product',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='product',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='productioncost',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='productioncost',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='productioncost',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='productioncost',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='productioncost',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='productioncost',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='productionmove',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='productionmove',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='productionmove',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='productionmove',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='productionmove',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='productionmove',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='productiontimeentry',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='productiontimeentry',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='productiontimeentry',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='productiontimeentry',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='productiontimeentry',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='productiontimeentry',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='publicholiday',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='publicholiday',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='publicholiday',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='publicholiday',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='publicholiday',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='publicholiday',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='qualitycontrolplan',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='qualitycontrolplan',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='qualitycontrolplan',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='qualitycontrolplan',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='qualitycontrolplan',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='qualitycontrolplan',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='qualitycontrolplanline',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='qualitycontrolplanline',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='qualitycontrolplanline',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='qualitycontrolplanline',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='qualitycontrolplanline',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='qualitycontrolplanline',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='qualityinspection',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='qualityinspection',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='qualityinspection',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='qualityinspection',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='qualityinspection',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='qualityinspection',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='qualityinspectionresult',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='qualityinspectionresult',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='qualityinspectionresult',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='qualityinspectionresult',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='qualityinspectionresult',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='qualityinspectionresult',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='reviewquestion',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='reviewquestion',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='reviewquestion',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='reviewquestion',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='reviewquestion',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='reviewquestion',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='reviewresponse',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='reviewresponse',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='reviewresponse',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='reviewresponse',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='reviewresponse',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='reviewresponse',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='routing',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='routing',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='routing',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='routing',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='routing',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='routing',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='routingoperation',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='routingoperation',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='routingoperation',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='routingoperation',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='routingoperation',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='routingoperation',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='salesforecast',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='salesforecast',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='salesforecast',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='salesforecast',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='salesforecast',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='salesforecast',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='team',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='team',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='team',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='team',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='team',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='team',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='timeentry',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='timeentry',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='timeentry',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='timeentry',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='timeentry',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='timeentry',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='unitofmeasure',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='unitofmeasure',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='unitofmeasure',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='unitofmeasure',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='unitofmeasure',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='unitofmeasure',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='vendor',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='vendor',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='vendor',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='vendor',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='vendor',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='vendor',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='vendorinvoice',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='vendorinvoice',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='vendorinvoice',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='vendorinvoice',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='vendorinvoice',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='vendorinvoice',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='vendorinvoiceline',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='vendorinvoiceline',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='vendorinvoiceline',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='vendorinvoiceline',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='vendorinvoiceline',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='vendorinvoiceline',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='vendorpayment',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='vendorpayment',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='vendorpayment',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='vendorpayment',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='vendorpayment',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='vendorpayment',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='warehouse',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='warehouse',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='warehouse',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='warehouse',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='warehouse',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='warehouse',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='workcenter',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='workcenter',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='workcenter',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='workcenter',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='workcenter',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='workcenter',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='workcentercalendar',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='workcentercalendar',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='workcentercalendar',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='workcentercalendar',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='workcentercalendar',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='workcentercalendar',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='workschedule',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Avatar'),
        ),
        migrations.AlterField(
            model_name='workschedule',
            name='created_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='workschedule',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datetime Created'),
        ),
        migrations.AlterField(
            model_name='workschedule',
            name='datetime_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datetime Updated'),
        ),
        migrations.AlterField(
            model_name='workschedule',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='workschedule',
            name='updated_by',
            field=bloomerp.model_fields.user_field.UserField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
    ]
