from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geography

revision = '0001_init'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.create_table('companies',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(length=200), nullable=False, unique=True),
        sa.Column('geofence_radius_m', sa.Integer, nullable=False, server_default='100'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'))
    )
    op.create_table('stores',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('company_id', sa.Integer, sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('address_lines', sa.Text),
        sa.Column('city', sa.String(length=120)),
        sa.Column('state', sa.String(length=120)),
        sa.Column('country', sa.String(length=120)),
        sa.Column('postal_code', sa.String(length=40)),
        sa.Column('location', Geography(geometry_type='POINT', srid=4326)),
        sa.Column('geocode_status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('custom_radius_m', sa.Integer),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'))
    )
    op.create_table('geocode_jobs',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('store_id', sa.Integer, sa.ForeignKey('stores.id'), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='queued'),
        sa.Column('provider', sa.String(length=40), nullable=False, server_default='google'),
        sa.Column('attempts', sa.Integer, nullable=False, server_default='0'),
        sa.Column('error_msg', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'))
    )
    op.create_table('tasks',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('store_id', sa.Integer, sa.ForeignKey('stores.id'), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('active', sa.Boolean, nullable=False, server_default=sa.text('true')),
        sa.Column('created_by', sa.String(length=120))
    )
    op.create_table('task_runs',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('task_id', sa.Integer, sa.ForeignKey('tasks.id'), nullable=False),
        sa.Column('worker_id', sa.String(length=120), nullable=False),
        sa.Column('client_location', Geography(geometry_type='POINT', srid=4326), nullable=False),
        sa.Column('distance_m', sa.Numeric(10,2), nullable=False),
        sa.Column('allowed', sa.Boolean, nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'))
    )

def downgrade():
    op.drop_table('task_runs')
    op.drop_table('tasks')
    op.drop_table('geocode_jobs')
    op.drop_table('stores')
    op.drop_table('companies')
    op.execute("DROP EXTENSION IF EXISTS postgis")

