# Create OpenAI GPT

This guide will walk you through the process of creating an OpenAI GPT.

## 1. Navigate to the OpenAI GPT creation page

To create a new OpenAI GPT, go to the following link:

[Create OpenAI GPT](https://chatgpt.com/gpts/editor)

## 2. Configure your GPT
)
Once you are on the creation page, click on "configure" and fill in the required details:

- **Name**: Choose a unique name for your GPT.
- **Description**: Provide a brief description of what your GPT does.

For the instructions, please copy the following template:

```
This GPT is a natural-language operational interface for the user’s BloomERP system, designed for non-technical users. It answers questions about BloomERP data and can safely create, update, or delete supported records through the available schema, SQL, and mutation actions.

Before answering a question that requires BloomERP data, retrieve the accessible tables at the start of each new conversation. Use the returned table names, columns, and metadata as the source of truth for read queries. Do not assume tables or columns that were not returned.

For read requests, identify the business intent, map it to accessible tables and fields, construct the safest appropriate read-only SQL query, execute it, validate the returned rows, and present a clear plain-language answer. Avoid showing raw SQL or raw result payloads unless the user asks.

Use read-only SQL by default. Never use SQL to modify data, including INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE, GRANT, REVOKE, or similar write or configuration statements. Perform data changes only through the BloomERP mutation endpoint and only when the user explicitly requests them. Before any create, update, or delete, retrieve the mutation catalog for the target resource, verify that the requested operation is available, and use only writable fields exposed by the catalog. For destructive, broad, ambiguous, or potentially irreversible changes, show a concise proposed-action summary covering the operation, target resource or scope, expected impact, and known irreversible effects, then wait for explicit confirmation. Straightforward low-risk creates or narrowly scoped updates may proceed when the user’s intent is already explicit.

When calling the BloomERP mutation endpoint, submit the mutation `data` argument as a JSON-encoded string, not as a nested JSON object. Build the resource payload internally as a normal object, serialize it exactly once using a JSON serializer, and pass the resulting serialized string as `data`. Ensure quotes, HTML attributes, line breaks, and backslashes inside string fields are escaped by the serializer. Do not manually concatenate JSON strings when a serializer is available. An error such as “Value must be valid JSON” should first trigger verification that the outer `data` value was serialized correctly; do not assume a rich-text field requires structured editor JSON. For updates and deletes, provide `resource`, `operation`, and `object_id` as normal tool arguments. Only the mutation payload in `data` should be JSON-encoded when required by the endpoint. Confirm mutation success only when the tool returns a successful response; never infer success from the absence of a visible error.

Prefer narrow, efficient queries. Select only needed columns, apply date ranges and filters when relevant, use reasonable limits for broad results, and handle pagination where supported. Be careful with sensitive employee or customer data, returning only what is necessary. For broad exports, highly sensitive data, or ambiguous requests that could expose unnecessary personal data, ask a focused clarification or offer an aggregated answer first.

When business terms are ambiguous, resolve them from accessible metadata when possible and state practical defaults. Interpret relative dates using the user’s relevant timezone when available. Explain the chosen basis briefly, and ask a focused clarification only when needed to avoid materially incorrect results.

When expandable details are supported, place a collapsed “How this was retrieved” section beneath the answer. Summarize the tables or mutation resource used, query or mutation purpose, key filters, limits, and assumptions. Redact secrets and unnecessary sensitive values. If expandable sections are unavailable, provide these details only when asked.

Never invent data, table names, columns, resource names, writable fields, permissions, mutation results, or query results. If required data or fields are unavailable, explain what is missing and suggest the closest supported action. If a query or mutation fails, use the returned error to revise the request only when safe and grounded in the accessible schema or mutation catalog; otherwise explain the failure plainly.

Communicate in a neutral, concise business tone. Prioritize practical answers over technical explanations while remaining transparent about assumptions, limitations, and the retrieval path.
```

## 3. Create an API key

Go to the API key management page in your BloomERP account:

[Create API Key](/users/api-keys/create/)

Copy that API key and temporarily store it somewhere.

## 4. Add a GPT action

Click on 'Add Action' in your BloomERP account to create a new GPT action.

```
openapi: 3.1.1
servers:
  - url: https://heertechis.bloomerp.io
info:
  title: ""
  version: 0.0.0
paths:
  /api/sql/accessible-tables/:
    get:
      operationId: sql_accessible_tables_retrieve
      tags:
        - sql
      security:
        - cookieAuth: []
        - basicAuth: []
        - {}
      responses:
        "200":
          description: No response body
  /api/sql/execute/:
    post:
      operationId: sql_execute_create
      description: Execute a SQL query and return the results in JSON format.
      tags:
        - sql
      requestBody:
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/ExecuteSqlRequest"
          application/x-www-form-urlencoded:
            schema:
              $ref: "#/components/schemas/ExecuteSqlRequest"
          multipart/form-data:
            schema:
              $ref: "#/components/schemas/ExecuteSqlRequest"
      security:
        - BloomerpApiKeyAuthentication: []
        - cookieAuth: []
        - basicAuth: []
      responses:
        "200":
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/ExecuteSqlResponse"
          description: ""
        "400":
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/ExecuteSqlErrorResponse"
          description: ""
        "403":
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/ExecuteSqlErrorResponse"
          description: ""
        "500":
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/ExecuteSqlErrorResponse"
          description: ""
  /api/mutations/:
    post:
      operationId: mutations_create
      description: Create, partially update, or delete one object exposed by BloomERP's generated model API. The resource is
        resolved server-side; this endpoint does not accept arbitrary URLs or HTTP methods.
      tags:
        - Assistant
      requestBody:
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/AssistantMutationRequest"
          application/x-www-form-urlencoded:
            schema:
              $ref: "#/components/schemas/AssistantMutationRequest"
          multipart/form-data:
            schema:
              $ref: "#/components/schemas/AssistantMutationRequest"
        required: true
      security:
        - BloomerpApiKeyAuthentication: []
        - cookieAuth: []
        - basicAuth: []
      responses:
        "200":
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/AssistantMutationResponse"
          description: ""
        "201":
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/AssistantMutationResponse"
          description: ""
        "400":
          content:
            application/json:
              schema:
                type: object
                additionalProperties: {}
                description: Unspecified response body
          description: ""
        "403":
          content:
            application/json:
              schema:
                type: object
                additionalProperties: {}
                description: Unspecified response body
          description: ""
        "404":
          content:
            application/json:
              schema:
                type: object
                additionalProperties: {}
                description: Unspecified response body
          description: ""
  /api/mutations/catalog/:
    get:
      operationId: mutations_catalog_retrieve
      description: List generated API resources, operations, and writable API fields available to the authenticated user.
        Results are paginated and can be filtered with search or an exact resource key. Use returned resource and field
        names with the Assistant Mutations endpoint.
      parameters:
        - in: query
          name: page
          schema:
            type: integer
          description: Page number, starting at 1.
        - in: query
          name: page_size
          schema:
            type: integer
          description: Resources per page. Defaults to 10 and may not exceed 50.
        - in: query
          name: resource
          schema:
            type: string
          description: Exact resource key, for example customers.
        - in: query
          name: search
          schema:
            type: string
          description: Case-insensitive search across resource keys, model names, and labels.
      tags:
        - Assistant
      security:
        - BloomerpApiKeyAuthentication: []
        - cookieAuth: []
        - basicAuth: []
      responses:
        "200":
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/AssistantMutationCatalogResponse"
          description: ""
components:
  schemas:
    ExecuteSqlErrorResponse:
      type: object
      properties:
        error:
          type: string
      required:
        - error
    ExecuteSqlRequest:
      type: object
      properties:
        query:
          type: string
          description: The SQL query to execute.
        page:
          type: integer
          minimum: 1
          default: 1
          description: The page number for paginated results.
        page_size:
          type: integer
          minimum: 1
          default: 25
          description: The number of rows per page.
    ExecuteSqlResponse:
      type: object
      properties:
        columns:
          type: array
          items:
            type: string
        rows:
          type: array
          items:
            type: object
            additionalProperties: {}
        row_count:
          type: integer
        page_rows_count:
          type: integer
        execution_ms:
          type: integer
        policy_message:
          type: string
          nullable: true
        page:
          type: integer
        page_size:
          type: integer
        total_pages:
          type: integer
        page_start:
          type: integer
        page_end:
          type: integer
        output_fields:
          type: object
          additionalProperties: {}
          nullable: true
      required:
        - columns
        - execution_ms
        - output_fields
        - page
        - page_end
        - page_rows_count
        - page_size
        - page_start
        - policy_message
        - row_count
        - rows
        - total_pages
    AssistantMutationCatalogResponse:
      type: object
      properties:
        resources:
          type: array
          items:
            type: object
            additionalProperties: {}
      required:
        - resources
    AssistantMutationRequest:
      type: object
      properties:
        resource:
          type: string
          description: The generated API resource key, for example `customers`.
        operation:
          allOf:
            - $ref: "#/components/schemas/OperationEnum"
          description: |-
            `update` applies a partial update to the target object.

            * `create` - create
            * `update` - update
            * `delete` - delete
        object_id:
          type: string
          description: The target object's primary key. Required for `update` and `delete`.
        data:
          description: An object containing the model fields to create or update.
      required:
        - operation
        - resource
    AssistantMutationResponse:
      type: object
      properties:
        resource:
          type: string
        operation:
          $ref: "#/components/schemas/OperationEnum"
        object:
          type: object
          additionalProperties: {}
        object_id:
          type: string
      required:
        - operation
        - resource
    OperationEnum:
      enum:
        - create
        - update
        - delete
      type: string
      description: |-
        * `create` - create
        * `update` - update
        * `delete` - delete
  securitySchemes:
    BloomerpApiKeyAuthentication:
      type: apiKey
      name: X-API-Key
      in: header

```



