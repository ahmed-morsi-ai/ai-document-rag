import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest import mock

import sqlalchemy as sa

from app.db.models import Base, Conversation, Message, User


MIGRATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "alembic"
    / "versions"
    / "d4f7a1b9c2e6_add_messages_table.py"
)


def load_migration_module():
    spec = importlib.util.spec_from_file_location(
        "add_messages_table_migration",
        MIGRATION_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class MessageModelTests(unittest.TestCase):
    def test_message_table_metadata_matches_required_schema(self):
        table = Message.__table__

        self.assertIs(
            Base.metadata.tables["messages"],
            table,
        )
        self.assertEqual(
            set(table.columns.keys()),
            {
                "id",
                "conversation_id",
                "role",
                "content",
                "sequence_number",
                "created_at",
            },
        )

        self.assertTrue(table.c.id.primary_key)
        self.assertFalse(table.c.conversation_id.nullable)
        self.assertTrue(table.c.conversation_id.index)
        self.assertFalse(table.c.role.nullable)
        self.assertEqual(
            table.c.role.type.length,
            20,
        )
        self.assertFalse(table.c.content.nullable)
        self.assertFalse(
            table.c.sequence_number.nullable,
        )
        self.assertFalse(table.c.created_at.nullable)

        foreign_key = next(
            iter(table.c.conversation_id.foreign_keys)
        )

        self.assertEqual(
            foreign_key.target_fullname,
            "conversations.id",
        )

    def test_message_constraints_are_configured(self):
        constraints = Message.__table__.constraints

        check_constraints = [
            constraint
            for constraint in constraints
            if isinstance(constraint, sa.CheckConstraint)
        ]
        unique_constraints = [
            constraint
            for constraint in constraints
            if isinstance(constraint, sa.UniqueConstraint)
        ]

        self.assertEqual(
            len(check_constraints),
            1,
        )
        self.assertIn(
            "role IN ('user', 'assistant')",
            str(check_constraints[0].sqltext),
        )

        self.assertEqual(
            len(unique_constraints),
            1,
        )
        self.assertEqual(
            unique_constraints[0].name,
            "uq_messages_conversation_sequence",
        )
        self.assertEqual(
            set(unique_constraints[0]._pending_colargs),
            {
                "conversation_id",
                "sequence_number",
            },
        )

    def test_conversation_messages_are_ordered_by_sequence_number(self):
        self.assertEqual(
            Conversation.messages.property.order_by,
            (Message.__table__.c.sequence_number,),
        )


    def test_role_constraint_allows_only_user_and_assistant(self):
        constraints = [
            constraint
            for constraint in Message.__table__.constraints
            if isinstance(constraint, sa.CheckConstraint)
        ]

        self.assertEqual(
            len(constraints),
            1,
        )
        self.assertIn(
            "role IN ('user', 'assistant')",
            str(constraints[0].sqltext),
        )

    def test_conversation_message_relationship_is_configured(self):
        self.assertIs(
            Message.conversation.property.mapper.class_,
            Conversation,
        )
        self.assertIs(
            Conversation.messages.property.mapper.class_,
            Message,
        )
        self.assertEqual(
            Message.conversation.property.back_populates,
            "messages",
        )
        self.assertEqual(
            Conversation.messages.property.back_populates,
            "conversation",
        )

    def test_valid_user_message_can_be_constructed(self):
        user = User(
            email="message-user@example.com",
            hashed_password="hashed",
        )
        conversation = Conversation(
            owner=user,
        )
        message = Message(
            conversation=conversation,
            role="user",
            content="hello",
            sequence_number=1,
        )

        self.assertIs(
            message.conversation,
            conversation,
        )
        self.assertEqual(
            message.role,
            "user",
        )
        self.assertEqual(
            message.content,
            "hello",
        )
        self.assertEqual(
            message.sequence_number,
            1,
        )

    def test_valid_assistant_message_can_be_constructed(self):
        conversation = Conversation()
        message = Message(
            conversation=conversation,
            role="assistant",
            content="hello back",
            sequence_number=2,
        )

        self.assertIs(
            message.conversation,
            conversation,
        )
        self.assertEqual(
            message.role,
            "assistant",
        )
        self.assertEqual(
            message.sequence_number,
            2,
        )

    def test_multiple_messages_have_explicit_ordering(self):
        conversation = Conversation()

        first = Message(
            conversation=conversation,
            role="user",
            content="first",
            sequence_number=1,
        )
        second = Message(
            conversation=conversation,
            role="assistant",
            content="second",
            sequence_number=2,
        )

        self.assertEqual(
            [first.sequence_number, second.sequence_number],
            [1, 2],
        )
        self.assertEqual(
            conversation.messages,
            [first, second],
        )


class MessageMigrationTests(unittest.TestCase):
    def test_migration_revision_chain_is_correct(self):
        migration = load_migration_module()

        self.assertEqual(
            migration.revision,
            "d4f7a1b9c2e6",
        )
        self.assertEqual(
            migration.down_revision,
            "c91d3e2f7a40",
        )

    def test_upgrade_creates_messages_table(self):
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
            "messages",
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
                "conversation_id",
                "role",
                "content",
                "sequence_number",
                "created_at",
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
            "conversations.id",
        )

        unique_constraints = [
            arg
            for arg in create_table_args[1:]
            if isinstance(arg, sa.UniqueConstraint)
        ]

        self.assertEqual(
            len(unique_constraints),
            1,
        )

        self.assertEqual(
            unique_constraints[0].name,
            "uq_messages_conversation_sequence",
        )
        self.assertEqual(
            list(unique_constraints[0]._pending_colargs),
            [
                "conversation_id",
                "sequence_number",
            ],
        )

        check_constraints = [
            arg
            for arg in create_table_args[1:]
            if isinstance(arg, sa.CheckConstraint)
        ]

        self.assertEqual(
            len(check_constraints),
            1,
        )
        self.assertIn(
            "role IN ('user', 'assistant')",
            str(check_constraints[0].sqltext),
        )

        operations.create_index.assert_called_once_with(
            "ix_messages_conversation_id",
            "messages",
            ["conversation_id"],
            unique=False,
        )

    def test_downgrade_drops_messages_index_and_table(self):
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
            "ix_messages_conversation_id",
            table_name="messages",
        )
        operations.drop_table.assert_called_once_with(
            "messages",
        )


if __name__ == "__main__":
    unittest.main()
