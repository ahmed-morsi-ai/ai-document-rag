import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest import mock

import sqlalchemy as sa

from app.db.models import Base, Document, User


MIGRATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "alembic"
    / "versions"
    / "b8e6d2f4a913_add_documents_table.py"
)


def load_migration_module():
    spec = importlib.util.spec_from_file_location(
        "add_documents_table_migration",
        MIGRATION_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class DocumentModelTests(unittest.TestCase):
    def test_document_table_metadata_matches_required_schema(self):
        table = Document.__table__

        self.assertIs(Base.metadata.tables["documents"], table)
        self.assertEqual(
            set(table.columns.keys()),
            {
                "id",
                "owner_id",
                "original_filename",
                "mime_type",
                "storage_path",
                "processing_status",
                "created_at",
                "updated_at",
            },
        )

        self.assertTrue(table.c.id.primary_key)
        self.assertFalse(table.c.owner_id.nullable)
        self.assertTrue(table.c.owner_id.index)
        self.assertEqual(table.c.original_filename.type.length, 255)
        self.assertEqual(table.c.mime_type.type.length, 255)
        self.assertEqual(table.c.storage_path.type.length, 1024)
        self.assertEqual(table.c.processing_status.type.length, 50)
        self.assertEqual(table.c.processing_status.default.arg, "uploaded")

        foreign_key = next(iter(table.c.owner_id.foreign_keys))

        self.assertEqual(foreign_key.target_fullname, "users.id")

    def test_user_document_relationship_is_configured(self):
        self.assertIs(Document.owner.property.mapper.class_, User)
        self.assertIs(User.documents.property.mapper.class_, Document)
        self.assertEqual(Document.owner.property.back_populates, "documents")
        self.assertEqual(User.documents.property.back_populates, "owner")


class DocumentMigrationTests(unittest.TestCase):
    def test_migration_depends_on_users_revision(self):
        migration = load_migration_module()

        self.assertEqual(migration.revision, "b8e6d2f4a913")
        self.assertEqual(migration.down_revision, "7c16b04319c9")

    def test_upgrade_creates_documents_table_and_owner_index(self):
        migration = load_migration_module()
        operations = SimpleNamespace(
            create_table=mock.Mock(),
            create_index=mock.Mock(),
            drop_index=mock.Mock(),
            drop_table=mock.Mock(),
            f=lambda name: name,
        )

        migration.op = operations
        migration.upgrade()

        operations.create_table.assert_called_once()
        create_table_args = operations.create_table.call_args.args

        self.assertEqual(create_table_args[0], "documents")

        column_names = {
            arg.name
            for arg in create_table_args[1:]
            if isinstance(arg, sa.Column)
        }

        self.assertEqual(
            column_names,
            {
                "id",
                "owner_id",
                "original_filename",
                "mime_type",
                "storage_path",
                "processing_status",
                "created_at",
                "updated_at",
            },
        )

        foreign_keys = [
            arg
            for arg in create_table_args[1:]
            if isinstance(arg, sa.ForeignKeyConstraint)
        ]

        self.assertEqual(len(foreign_keys), 1)
        self.assertEqual(
            list(foreign_keys[0].elements)[0].target_fullname,
            "users.id",
        )
        operations.create_index.assert_called_once_with(
            "ix_documents_owner_id",
            "documents",
            ["owner_id"],
            unique=False,
        )

    def test_downgrade_drops_owner_index_and_documents_table(self):
        migration = load_migration_module()
        operations = SimpleNamespace(
            create_table=mock.Mock(),
            create_index=mock.Mock(),
            drop_index=mock.Mock(),
            drop_table=mock.Mock(),
            f=lambda name: name,
        )

        migration.op = operations
        migration.downgrade()

        operations.drop_index.assert_called_once_with(
            "ix_documents_owner_id",
            table_name="documents",
        )
        operations.drop_table.assert_called_once_with("documents")


if __name__ == "__main__":
    unittest.main()
