import importlib
from types import SimpleNamespace

from django.test import SimpleTestCase

from bloomerp.automation.registry import (
    WORKFLOW_NODE_REGISTRY,
    WorkflowNodeDefinition,
)
from bloomerp.models.automation.workflow_node import WorkflowNode
from bloomerp.serializers.workflow import WorkflowNodeSerializer


class TestWorkflowNodeRegistry(SimpleTestCase):
    def test_extensions_can_register_nodes_for_every_supported_type(self):
        """
        Use case: An extension contributes trigger, action, and flow node subtypes.
        Expected result: Every subtype is available through the same flat registry.
        """
        # 1. Register one extension node for each supported node type.
        definitions = [
            WorkflowNodeDefinition(
                id=f"EXTENSION_{node_type}",
                type=node_type,
                name=f"Extension {node_type.title()}",
                description="Extension-provided workflow node.",
            )
            for node_type in ("TRIGGER", "ACTION", "FLOW")
        ]
        for definition in definitions:
            WORKFLOW_NODE_REGISTRY.register(definition.id, definition)
            self.addCleanup(WORKFLOW_NODE_REGISTRY.unregister, definition.id)

        # 2. Confirm lookup, grouping, and lazy model choices all use the registry.
        grouped = {
            group["id"]: {node.id for node in group["nodes"]}
            for group in WORKFLOW_NODE_REGISTRY.grouped()
        }
        choices = WorkflowNode._meta.get_field("sub_type").flatchoices
        for definition in definitions:
            self.assertIs(WORKFLOW_NODE_REGISTRY.get(definition.id), definition)
            self.assertIn(definition.id, grouped[definition.type])
            self.assertIn((definition.id, definition.name), choices)

    def test_serializer_rejects_a_subtype_from_another_node_type(self):
        """
        Use case: A payload combines an action subtype with the trigger category.
        Expected result: Validation reports the category/subtype mismatch.
        """
        # 1. Validate a deliberately mismatched node payload.
        serializer = WorkflowNodeSerializer(
            data={
                "client_id": "node-1",
                "type": "TRIGGER",
                "sub_type": "SEND_EMAIL",
                "parameters": {},
            }
        )

        # 2. Confirm the invalid relationship is rejected.
        self.assertFalse(serializer.is_valid())
        self.assertIn("sub_type", serializer.errors)

    def test_duplicate_persisted_node_ids_are_rejected(self):
        """
        Use case: An extension registers a node ID already owned by core.
        Expected result: The registry rejects the ambiguous persisted ID.
        """
        # 1. Construct a definition whose key collides with a built-in node.
        duplicate = WorkflowNodeDefinition(
            id="SEND_EMAIL",
            type="ACTION",
            name="Alternative Email",
            description="Invalid duplicate node.",
        )

        # 2. Verify duplicate persisted IDs cannot be registered.
        with self.assertRaisesMessage(ValueError, "'SEND_EMAIL' is already registered"):
            WORKFLOW_NODE_REGISTRY.register("EXTENSION_EMAIL", duplicate)

    def test_registry_rejects_new_top_level_node_types(self):
        """
        Use case: An extension attempts to add a fourth top-level node category.
        Expected result: The registry keeps the public type contract to three literals.
        """
        # 1. Construct a definition with an unsupported runtime category.
        definition = WorkflowNodeDefinition(
            id="EXTENSION_UNKNOWN",
            type="UNKNOWN",
            name="Unknown",
            description="Invalid top-level category.",
        )

        # 2. Confirm runtime registration enforces the Literal contract too.
        with self.assertRaisesMessage(ValueError, "Unsupported workflow node type"):
            WORKFLOW_NODE_REGISTRY.register("EXTENSION_UNKNOWN", definition)


class TestFlattenWorkflowNodeConfigurationMigration(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.migration = importlib.import_module(
            "bloomerp.migrations.0063_flatten_workflow_node_configuration"
        )

    def test_migration_copies_sub_type_and_parameters_exactly(self):
        """
        Use case: A production node has the confirmed config wrapper shape.
        Expected result: Its subtype and parameters move to separate fields unchanged.
        """
        # 1. Provide a historical-model stand-in with the production config shape.
        parameters = {"recipient": "person@example.com", "nested": {"enabled": True}}
        node = SimpleNamespace(
            pk=42,
            config={"sub_type": "SEND_EMAIL", "parameters": parameters},
        )
        node.save = lambda **kwargs: setattr(node, "saved_with", kwargs)
        model = SimpleNamespace(
            objects=SimpleNamespace(
                all=lambda: SimpleNamespace(iterator=lambda: iter([node]))
            )
        )
        apps = SimpleNamespace(get_model=lambda *args: model)

        # 2. Run the migration and verify it performs an exact, explicit copy.
        self.migration.flatten_workflow_node_configuration(apps, None)
        self.assertEqual(node.sub_type, "SEND_EMAIL")
        self.assertIs(node.parameters, parameters)
        self.assertEqual(
            node.saved_with,
            {"update_fields": ["sub_type", "parameters"]},
        )

    def test_migration_fails_when_confirmed_fields_are_missing(self):
        """
        Use case: A node unexpectedly lacks parameters despite the production audit.
        Expected result: Migration stops loudly instead of inventing fallback data.
        """
        # 1. Provide an invalid row that violates the confirmed production shape.
        node = SimpleNamespace(pk=99, config={"sub_type": "SEND_EMAIL"})
        model = SimpleNamespace(
            objects=SimpleNamespace(
                all=lambda: SimpleNamespace(iterator=lambda: iter([node]))
            )
        )
        apps = SimpleNamespace(get_model=lambda *args: model)

        # 2. Confirm the migration exposes the bad row explicitly.
        with self.assertRaisesMessage(ValueError, "config is missing parameters"):
            self.migration.flatten_workflow_node_configuration(apps, None)
