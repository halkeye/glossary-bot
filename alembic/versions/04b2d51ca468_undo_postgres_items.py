"""undo postgres items

Revision ID: 04b2d51ca468
Revises: 201bae6698f6
Create Date: 2023-08-16 19:46:06.705898

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "04b2d51ca468"
down_revision = "201bae6698f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    db_bind = op.get_bind()
    if db_bind.engine.name != "postgresql":
        return

    #
    # Revert the terms index to the original style
    #

    # drop the varchar_pattern_ops index
    db_bind.execute(
        sa.sql.text(
            """
        DROP INDEX IF EXISTS ix_definitions_term;
    """
        )
    )
    # re-create the standard index
    db_bind.execute(
        sa.sql.text(
            """
        CREATE INDEX ix_definitions_term ON definitions(term);
    """
        )
    )

    #
    # Remove support for full-text search on terms and definitions
    #

    # drop the tsv_search column from the definitions table
    db_bind.execute(
        sa.sql.text(
            """
        ALTER TABLE definitions DROP COLUMN IF EXISTS tsv_search;
    """
        )
    )

    # drop the search trigger and function
    db_bind.execute(
        sa.sql.text(
            """
        DROP TRIGGER IF EXISTS tsvupdate_definitions_trigger ON definitions;
    """
        )
    )
    db_bind.execute(
        sa.sql.text(
            """
        DROP FUNCTION IF EXISTS definitions_search_trigger();
    """
        )
    )

    # drop the index
    db_bind.execute(
        sa.sql.text(
            """
        DROP INDEX IF EXISTS ix_definitions_tsv_search;
    """
        )
    )


def downgrade() -> None:
    db_bind = op.get_bind()
    if db_bind.engine.name != "postgresql":
        return
    #
    # Replace the index for terms with one including varchar_pattern_ops
    #

    # drop the old index
    db_bind.execute(
        sa.sql.text(
            """
        DROP INDEX IF EXISTS ix_definitions_term;
    """
        )
    )
    # create the new index
    db_bind.execute(
        sa.sql.text(
            """
        CREATE INDEX ix_definitions_term ON definitions (term varchar_pattern_ops);
    """
        )
    )

    #
    # Support full-text search on terms and definitions
    #

    # add the tsv_search column to the definitions table
    db_bind.execute(
        sa.sql.text(
            """
        ALTER TABLE definitions ADD COLUMN tsv_search tsvector;
    """
        )
    )

    # set up a trigger to populate tsv_search when records are created or altered
    db_bind.execute(
        sa.sql.text(
            """
        DROP FUNCTION IF EXISTS definitions_search_trigger();
    """
        )
    )
    db_bind.execute(
        sa.sql.text(
            """
        CREATE FUNCTION definitions_search_trigger() RETURNS trigger AS $$
        begin
          new.tsv_search :=
             setweight(to_tsvector('pg_catalog.english', COALESCE(new.term,'')), 'A') ||
             setweight(to_tsvector('pg_catalog.english', COALESCE(new.definition,'')), 'B');
          return new;
        end
        $$ LANGUAGE plpgsql;
    """
        )
    )

    db_bind.execute(
        sa.sql.text(
            """
        DROP TRIGGER IF EXISTS tsvupdate_definitions_trigger ON definitions;
    """
        )
    )
    db_bind.execute(
        sa.sql.text(
            """
        CREATE TRIGGER tsvupdate_definitions_trigger BEFORE INSERT OR UPDATE ON definitions FOR EACH ROW EXECUTE PROCEDURE definitions_search_trigger();
    """
        )
    )

    # create an index for tsv_search
    db_bind.execute(
        sa.sql.text(
            """
        DROP INDEX IF EXISTS ix_definitions_tsv_search;
    """
        )
    )
    db_bind.execute(
        sa.sql.text(
            """
        CREATE INDEX ix_definitions_tsv_search ON definitions USING gin(tsv_search);
    """
        )
    )

    # populate tsv_search for existing records
    db_bind.execute(
        sa.sql.text(
            """
        UPDATE definitions SET tsv_search = setweight(to_tsvector('pg_catalog.english', COALESCE(term,'')), 'A') || setweight(to_tsvector('pg_catalog.english', COALESCE(definition,'')), 'B');
    """
        )
    )
