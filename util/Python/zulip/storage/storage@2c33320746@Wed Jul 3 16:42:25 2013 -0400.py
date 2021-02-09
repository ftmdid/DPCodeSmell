from django.conf import settings
from django.contrib.staticfiles.storage import CachedFilesMixin, StaticFilesStorage
from pipeline.storage import PipelineMixin
import os.path
import ujson

class AddHeaderMixin(object):
    def post_process(self, paths, dry_run=False, **kwargs):
        if dry_run:
            return

        with open(settings.STATIC_HEADER_FILE) as header_file:
            header = header_file.read().decode(settings.FILE_CHARSET)

        # A dictionary of path to tuples of (old_path, new_path,
        # processed).  The return value of this method is the values
        # of this dictionary
        ret_dict = {}

        for name in paths:
            storage, path = paths[name]

            if not path.startswith('min/') or not path.endswith('.css'):
                ret_dict[path] = (path, path, False)
                continue

            # Prepend the header
            with storage.open(path) as orig_file:
                orig_contents = orig_file.read().decode(settings.FILE_CHARSET)

            storage.delete(path)

            with storage.open(path, 'w') as new_file:
                new_file.write(header + orig_contents)

            ret_dict[path] = (path, path, True)

        super_class = super(AddHeaderMixin, self)
        if hasattr(super_class, 'post_process'):
            super_ret = super_class.post_process(paths, dry_run, **kwargs)
        else:
            super_ret = []

        # Merge super class's return value with ours
        for val in super_ret:
            old_path, new_path, processed = val
            if processed:
                ret_dict[old_path] = val

        return ret_dict.itervalues()


class DumpManifestMixin(object):
    """ This mixin creates a JSON manifest file in the deployment root
    with a dict mapping generated files' base names (like api.js) to their
    names with the hash for the most recent version (api.HEX_HASH_HERE.js).
    """
    def post_process(self, paths, dry_run=False, **kwargs):
        if dry_run:
            return

        super_class = super(DumpManifestMixin, self)
        if hasattr(super_class, 'post_process'):
            super_ret = super_class.post_process(paths, dry_run, **kwargs)
        else:
            super_ret = []

        hashed_versions = {}  # Latest hashed version of each file.
        for old_path, new_path, processed in super_ret:
            if old_path[:4] == 'min/':
                hashed_versions[old_path] = new_path

        manifest_filename = os.path.join(settings.DEPLOY_ROOT,
                'minified_assets.json')
        with open(manifest_filename, 'w') as manifest_file:
            manifest_file.write(ujson.dumps(hashed_versions))

        return super_ret


class HumbugStorage(PipelineMixin, AddHeaderMixin, DumpManifestMixin,
        CachedFilesMixin, StaticFilesStorage):
    pass