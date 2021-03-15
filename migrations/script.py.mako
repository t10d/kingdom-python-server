"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
import sqlalchemy as sa
${imports if imports else ""}
from alembic import op, context

# revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade():
    schema_upgrade()
    if context.get_x_argument(as_dictionary=True).get('data'):
        data_upgrade()

def downgrade():
    if context.get_x_argument(as_dictionary=True).get('data'):
        data_downgrade()
    schema_downgrade()


def schema_upgrade():
    ${upgrades if upgrades else "pass"}


def schema_downgrade():
    ${downgrades if downgrades else "pass"}


def data_upgrade():
    pass

def data_downgrade():
    pass
