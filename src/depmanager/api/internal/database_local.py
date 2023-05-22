"""
Local database object.
"""
from pathlib import Path
from depmanager.api.internal.database_common import __DataBase, Dependency

packing_formats = ["tgz", "zip"]


class LocalDatabase(__DataBase):
    """
    Database stored in the local machine.
    """

    def __init__(self, base_path: Path, verbosity:int  = 0):
        super().__init__(verbosity)
        self.base_path = Path()
        if not base_path.exists():
            self.valid_shape = False
            return
        if not base_path.is_dir():
            self.valid_shape = False
            return
        self.base_path = base_path
        self.reload()

    def reload(self):
        """
        Reload database by analysing the folder.
        """
        if self.valid_shape:
            for depend in self.base_path.iterdir():
                dep = Dependency(depend)
                if not dep.valid:
                    continue
                self.dependencies.append(dep)

    def delete(self, deps):
        """
        Remove all package matching deps.
        :param deps: Query for deletion.
        """
        from shutil import rmtree
        for dep in self.query(deps):
            path = self.base_path / dep.get_path()
            rmtree(path)

    def pack(self, deps, destination: Path, archive_format: str = packing_formats[0]):
        """
        Compress the Dependencies.
        :param deps: Query for deletion.
        :param destination: Folder where to put the files.
        :param archive_format: Archive's type.
        """
        from zipfile import ZipFile, ZIP_DEFLATED
        import tarfile
        if archive_format not in packing_formats:
            archive_format = packing_formats[0]
        for dep in self.query(deps):
            dep_path = self.base_path / dep.get_path()
            archive_name = destination / (dep_path.name + f".{archive_format}")
            archive_name.parent.mkdir(parents=True, exist_ok=True)
            if archive_format == "zip":
                with ZipFile(archive_name, "w", ZIP_DEFLATED) as zip_file:
                    for content in dep_path.rglob("*"):
                        zip_file.write(content, content.relative_to(dep_path))
            elif archive_format == "tgz":
                with tarfile.open(str(archive_name), "w|gz") as tar_file:
                    tar_file.add(dep_path, dep_path.relative_to(dep_path))
