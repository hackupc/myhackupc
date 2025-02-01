import os
from django.core.exceptions import ValidationError
from django.conf import settings


def validate_file_extension(value):
    (_, ext) = os.path.splitext(value.name)
    valid_extensions = getattr(settings, 'SUPPORTED_RESUME_EXTENSIONS', None)
    if valid_extensions and not ext.lower() in valid_extensions:
        raise ValidationError('Unsupported file extension.')


def validate_file_extension_size(value):
    (_, ext) = os.path.splitext(value.name)
    valid_extensions = getattr(settings, 'SUPPORTED_RESUME_EXTENSIONS', None)
    if valid_extensions and not ext.lower() in valid_extensions:
        raise ValidationError('Unsupported file extension.')
    elif value.size > settings.MAX_UPLOAD_SIZE:
        raise ValidationError(
            f'Please keep resume size under {settings.MAX_UPLOAD_SIZE / (1024 * 1024):.2f}MB. '
            f'Current filesize: {value.size / (1024 * 1024):.2f}MB'
        )
