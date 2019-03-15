from django.contrib.staticfiles.storage import StaticFilesStorage
from django.contrib.staticfiles.storage import ManifestStaticFilesStorage
from whitenoise.storage import CompressedStaticFilesStorage
from whitenoise.storage import CompressedManifestStaticFilesStorage

class StaticFilesStorage(StaticFilesStorage):
	pass

class ManifestStaticFilesStorage(ManifestStaticFilesStorage):
	# Disable strict cache manifest checking
    manifest_strict = False

class CompressedStaticFilesStorage(CompressedStaticFilesStorage):
	pass

class CompressedManifestStaticFilesStorage(CompressedManifestStaticFilesStorage):
	# Disable strict cache manifest checking
    manifest_strict = False
