import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest import mock

import sqlalchemy as sa

from app.db.models import Base, Conversation, User


MIGRATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "alembic"
    / "versions"
    / "c91d3e2f7a40_add_conversations_table.py"
)


def load_migration_module():
    spec = importlib.util.spec_from_file_location(
        "add_conversations_table_migration",
        MIGRATION_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ConversationModelTests(unittest.TestCase):
    def test_conversation_table_metadata_matches_required_schema(self):
        table = Conversation.__table__

        self.assertIs(
            Base.metadata.tables["conversations"],
            table,
        )
        self.assertEqual(
            set(table.columns.keys()),
            {
                "id",
                "owner_id",
                "created_at",
                "updated_at",
            },
        )

        self.assertTrue(table.c.id.primary_key)
        self.assertFalse(table.c.owner_id.nullable)
        self.assertTrue(table.c.owner_id.index)
        self.assertFalse(table.c.created_at.nullable)
        self.assertFalse(table.c.updated_at.nullable)

        foreign_key = next(
            iter(table.c.owner_id.foreign_keys)
        )

        self.assertEqual(
            foreign_key.target_fullname,
            "users.id",
        )

    def test_user_conversation_relationship_is_configured(self):
        self.assertIs(
            Conversation.owner.property.mapper.class_,
            User,
        )
        self.assertIs(
            User.conversations.property.mapper.class_,
            Conversation,
        )
        self.assertEqual(
            Conversation.owner.property.back_populates,
            "conversations",
        )
        self.assertEqual(
            User.conversations.property.back_populates,
            "owner",
        )

    def test_conversation_can_be_constructed_for_existing_user(self):
        user = User(
            email="conversation@example.com",
            hashed_password="hashed",
        )
        conversation = Conversation(
            owner=user,
        )

        self.assertIs(
            conversation.owner,
            user,
        )
        self.assertFalse(
            Conversation.__table__.c.owner_id.nullable,
        )


class ConversationMigrationTests(unittest.TestCase):
    def test_migration_revision_chain_is_correct(self):
        migration = load_migration_module()

        self.assertEqual(
            migration.revision,
            "c91d3e2f7a40",
        )
        self.assertEqual(
            migration.down_revision,
            "b8e6d2f4a913",
        )

    def test_upgrade_creates_conversations_table_and_owner_index(
        self,
    ):
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

        create_table_args = (
            operations.create_table.call_args.args
        )

        self.assertEqual(
            create_table_args[0],
            "conversations",
        )

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
                "created_at",
                "updated_at",
            },
        )

        foreign_keys = [
            arg
            for arg in create_table_args[1:]
            if isinstance(arg, sa.ForeignKeyConstraint)
        ]

        self.assertEqual(
            len(foreign_keys),
            1,
        )
        self.assertEqual(
            list(foreign_keys[0].elements)[0].target_fullname,
            "users.id",
        )

        operations.create_index.assert_called_once_with(
            "ix_conversations_owner_id",
            "conversations",
            ["owner_id"],
            unique=False,
        )

    def test_downgrade_drops_owner_index_and_conversations_table(
        self,
    ):
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
            "ix_conversations_owner_id",
            table_name="conversations",
        )
        operations.drop_table.assert_called_once_with(
            "conversations",
        )


if __name__ == "__main__":
    unittest.main()
