from bloomerp.services.permission_services import UserPermissionManager
from bloomerp.services.sql_services import SqlExecutor
from bloomerp.tests.base import BaseBloomerpModelTestCase
from bloomerp.utils.sql import SqlQueryExecutor
from unittest.mock import patch

class TestSQLServices(BaseBloomerpModelTestCase):
    create_foreign_models = True
    
    CUSTOMER_TABLE : str
    PLANET_TABLE : str
    
    def extendedSetup(self):
        self.CUSTOMER_TABLE = self.CustomerModel._meta.db_table
        self.PLANET_TABLE = self.PlanetModel._meta.db_table
        
        self.executor = SqlExecutor(self.admin_user)        
        return super().extendedSetup()
    
    # -----------------------------
    # TEST UNSAFE QUERIES
    # -----------------------------
    def test_unsafe_query_drop(self):
        """
        UC: As a user I want to be prevented from executing unsafe queries
        
        Expected Result: Query should be flagged as unsafe if it can modify the database structure or data.
        """
        # 1. Create query
        query = f"""
        DROP TABLE {self.CUSTOMER_TABLE};
        """
        
        # 2. Check if flagged as unsafe
        self.assertFalse(
            self.executor.is_safe(query)
        )
        
    def test_unsafe_query_delete(self):
        """
        UC: As a user I want to be prevented from executing unsafe DELETE queries
        
        Expected Result: Query should be flagged as unsafe if it can modify the database structure or data.
        """
        query = f"""
        DELETE FROM {self.CUSTOMER_TABLE} WHERE id = 1;
        """
        self.assertFalse(self.executor.is_safe(query))

    def test_unsafe_query_truncate(self):
        """
        UC: As a user I want to be prevented from executing unsafe TRUNCATE queries

        Expected Result: Query should be flagged as unsafe if it can modify the database structure or data.
        """
        query = f"""
        TRUNCATE TABLE {self.CUSTOMER_TABLE};
        """
        self.assertFalse(self.executor.is_safe(query))

    def test_unsafe_query_alter(self):
        """
        UC: As a user I want to be prevented from executing unsafe ALTER TABLE queries

        Expected Result: Query should be flagged as unsafe if it can modify the database structure or data.
        """
        query = f"""
        ALTER TABLE {self.CUSTOMER_TABLE} DROP COLUMN name;
        """
        self.assertFalse(self.executor.is_safe(query))

    def test_safe_query_select(self):
        """
        UC: As a user I want to be able to execute safe SELECT queries

        Expected Result: Query should be flagged as safe if it does not modify the database structure or data.
        """
        query = f"""
        SELECT * FROM {self.CUSTOMER_TABLE};
        """
        self.assertTrue(self.executor.is_safe(query))

    def test_extract_referenced_tables_ignores_cte_names(self):
        """
        Tests whether CTE aliases are not treated as database tables.
        """
        query = f"""
        WITH bloomerp_kpi_source AS (
            SELECT id FROM {self.CUSTOMER_TABLE}
        ),
        bloomerp_kpi_numbered AS (
            SELECT * FROM bloomerp_kpi_source
        )
        SELECT COUNT("id") FROM bloomerp_kpi_numbered;
        """

        self.assertEqual(
            self.executor._extract_referenced_tables(query),
            {self.CUSTOMER_TABLE},
        )

    def test_raw_postgres_type_code_falls_back_to_backend_type_map(self):
        """
        Tests whether raw cursor type codes still resolve when introspection fails.
        """
        executor = SqlQueryExecutor()

        with patch(
            "bloomerp.utils.sql.connection.introspection.get_field_type",
            side_effect=AttributeError("raw cursor metadata"),
        ), patch(
            "bloomerp.utils.sql.connection.introspection.data_types_reverse",
            {701: "FloatField"},
        ):
            field_type = executor._get_field_type((None, 701))

        self.assertEqual(field_type, "floatfield")
    
    # -----------------------------
    # TEST RESOLVERS
    # -----------------------------
    def test_output_field_type_uses_numeric_row_value_when_metadata_is_unknown(self):
        """
        Tests whether computed numeric columns are not downgraded without metadata.
        """
        field_type = self.executor._resolve_output_field_type(
            "total",
            "unknown",
            [{"total": 12.5}],
        )

        self.assertEqual(field_type, "numeric")

    def test_output_field_type_keeps_text_when_metadata_and_value_are_text(self):
        """
        Tests whether real text columns stay text when sampled.
        """
        field_type = self.executor._resolve_output_field_type(
            "activity",
            "text",
            [{"activity": "Development"}],
        )

        self.assertEqual(field_type, "text")

    def test_output_field_type_does_not_assume_id_columns_are_numeric(self):
        """
        Tests whether ID column names alone do not force numeric output types.
        """
        field_type = self.executor._resolve_output_field_type(
            "external_id",
            "unknown",
            [],
        )

        self.assertEqual(field_type, "text")
    
    def test_sql_query_resolves_current_user(self):
        """
        UC: As a user, I want to be able to build queries that resolve to particular users
        
        Expected Result: the 'current_user' attribute should resolve to the user executing the query
        """
        #1. Create specific object
        self.create_customer(first_name="Wesley", last_name="Snipes", age=60, created_by=self.admin_user)
        
        # 2. Create query that uses current_user
        query = f"""
        SELECT * FROM {self.CUSTOMER_TABLE} WHERE created_by = '{{current_user}}';
        """
        
        # 3. Execute query and check results
        executor = SqlExecutor(self.admin_user)
        result = executor.execute_query(query)
        self.assertIsNotNone(result)
        
        self.assertEqual(
            len(result), 1, "Expected one customer created by the admin user"
        )
        
        self.assertEqual(
            result[0]["first_name"], "Wesley", "Expected the first name of the customer to be 'Wesley'"
        )
        
        
    # -----------------------------
    # TEST USER ACCESS TO TABLES
    # -----------------------------
    def test_user_can_only_access_tables_to_which_he_has_global_view_access(self):
        """
        UC: As a user I want to access tables which lie in my permissions
        
        Expected Result: User should only be able to access tables to which he has global view
        permission
        """
        #1. Assign global view permissions

        #2. Construct query to access tables
    
    def test_admin_user_can_access_all_tables_and_fields(self):
        """
        UC: As an admin user, I want to be able to frealy perform (safe) sql queries
        
        Expected Result: Admin user can access al tables
        """
        #1. Construct sql query
        query = f"SELECT * FROM {self.CUSTOMER_TABLE}"
        
        #2. Execute query and check results
        executor = SqlExecutor(self.admin_user)
        
        #3. Execute query and check results
        result = executor.execute_query(query)
        
        #4. Assert
        self.assertIsNotNone(result)
        
    def test_user_can_only_access_fields_for_which_he_has_field_policy_access(self):
        """
        UC: As a user I want to access certain fields in tables
        
        Expected Result: User should be allowed to access fields of certain tables
        if he has field-level permissions for that.
        """
        # 0. Create a customer row created by another user
        self.create_customer(first_name="John", last_name="Doe", age=30, created_by=self.normal_user)
            
        #1. Assign permissions
        manager = UserPermissionManager(self.normal_user)
        manager.assign_creator_permission(
            self.CustomerModel,
            field_policy={
                "first_name" : SqlExecutor.REQUIRED_PERMISSION,
                "last_name" : SqlExecutor.REQUIRED_PERMISSION,
            },
            row_permissions="__all__"
        )
        
        #2. Construct query to access fields of a table
        query = f"SELECT first_name, last_name, age, created_by FROM {self.CUSTOMER_TABLE}"
        
        #3. Execute query and check results
        executor = SqlExecutor(self.normal_user)
        result = executor.execute_query(query)
        
        #4. Assert
        self.assertIsNotNone(result)
        self.assertEqual(
            len(result.rows), 1, "Expected no customers since the user has no rows created by him"
        )
        self.assertEqual(
            result.rows[0]["first_name"], "John", "Expected the first name of the customer to be 'John'"
        )
        
        self.assertIn(
            "first_name", result.rows[0], "Expected the first name of the customer to be present"
        )
        self.assertIn(
            "last_name", result.rows[0], "Expected the last name of the customer to be present"
        )
        self.assertNotIn(
            "age", result.rows[0], "Expected the age of the customer to be filtered out due to lack of field-level permission"
        )
        
    def test_user_has_least_privelege_to_certain_field(self):
        """
        UC: Users can sometimes have multiple policies, whereby each policy gives access to certain fields.
        Example:
            - Policy 1: gives access to fields 'first_name' and 'last_name' and row level access to id=1
            - Policy 2: gives access to fields 'age' and 'created_by' and row level access to id=2
        
        
        Expected Result: table is returned that gives least access
        """
        
        #1. Create policies and assign to user
        
    
        
    