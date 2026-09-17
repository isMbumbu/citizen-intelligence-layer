# TAX-001: Project category reference data

## Goal

Introduce a flexible public-project taxonomy that supports how Kenyan public
project data is actually categorized, while avoiding the rigidity of a single
static enum.

## User

Developer / reviewer / product operator

## Context

The current project type model is too narrow for realistic public spending and
project management. A database-managed category structure is needed to support
real-world categories, subtypes, and future analytics.

## Requirements

- Create project category reference data with a parent/child relationship.
- Add a subtype layer for more specific project types.
- Categories and subtypes remain active/inactive as needed.
- The model supports county and national project use cases.
- The implementation supports future filtering and analytics without deployment
  churn.

## Acceptance criteria

### AC1: Reference data supports hierarchy
Given a category with subtypes exists
When the project taxonomy is queried
Then the hierarchy is returned clearly.

### AC2: Projects can reference a category and optional subtype
Given a project record is created
When category metadata is attached
Then the project can be grouped and filtered by category.

### AC3: Category management does not require application redeployment
Given a new public project type is added as reference data
When the data set is updated
Then the application can expose the new type without code changes.

## Data requirements

- `ProjectCategory`
- `ProjectSubtype`
- project relationship to category/subtype

## API requirements

- `GET /project-categories`
- `GET /project-categories/{category_id}/subtypes`

## UI requirements

- filter controls by category and subtype
- project detail category labeling

## Security requirements

- category data is administrative reference data and must not be user-editable
  without authorization

## Provenance requirements

- category metadata is administrative reference data and is not a public-source
  fact by itself

## Tests

- category hierarchy loads correctly
- subtype relationship resolves correctly
- project filtering by category works

## Dependencies

- FND-001
- FND-002

## Non-goals

- not a full GIS taxonomy
- not a national registry integration
- not analytical dashboards beyond category filtering

## Definition of done

- category data model is in place
- project taxonomy is flexible and extendable
- category data can support future project filtering and reporting
