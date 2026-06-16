# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools


class MediflowVQueueMetrics(models.Model):
    """Read-only SQL view: one row per queue entry with derived wait/service
    minutes, used by the Operational Throughput dashboard (docs 08 §1). All
    aggregation (avg, count, no-show rate, throughput) is done by read_group on
    top of this view so PostgreSQL does the heavy lifting at 1M-record scale."""

    _name = "mediflow.v.queue.metrics"
    _description = "Queue Metrics (view)"
    _auto = False
    _order = "created_at desc"

    id = fields.Integer(readonly=True)
    company_id = fields.Many2one("res.company", string="Clinic", readonly=True)
    queue_id = fields.Many2one("mediflow.queue", string="Service Point", readonly=True)
    state = fields.Selection([
        ("waiting", "Waiting"),
        ("called", "Called"),
        ("serving", "Serving"),
        ("done", "Done"),
        ("no_show", "No-show"),
    ], readonly=True)
    created_at = fields.Datetime(readonly=True)
    called_at = fields.Datetime(readonly=True)
    serving_at = fields.Datetime(readonly=True)
    done_at = fields.Datetime(readonly=True)
    wait_minutes = fields.Float(string="Wait (min)", readonly=True, aggregator="avg")
    service_minutes = fields.Float(string="Service (min)", readonly=True,
                                   aggregator="avg")
    is_no_show = fields.Integer(string="No-show", readonly=True, aggregator="sum")
    is_done = fields.Integer(string="Completed", readonly=True, aggregator="sum")
    entry_count = fields.Integer(string="Entries", readonly=True, aggregator="sum")

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    e.id                AS id,
                    e.company_id        AS company_id,
                    e.queue_id          AS queue_id,
                    e.state             AS state,
                    e.created_at        AS created_at,
                    e.called_at         AS called_at,
                    e.serving_at        AS serving_at,
                    e.done_at           AS done_at,
                    CASE WHEN e.called_at IS NOT NULL AND e.created_at IS NOT NULL
                         THEN EXTRACT(EPOCH FROM (e.called_at - e.created_at)) / 60.0
                         ELSE NULL END  AS wait_minutes,
                    CASE WHEN e.done_at IS NOT NULL AND e.serving_at IS NOT NULL
                         THEN EXTRACT(EPOCH FROM (e.done_at - e.serving_at)) / 60.0
                         ELSE NULL END  AS service_minutes,
                    CASE WHEN e.state = 'no_show' THEN 1 ELSE 0 END AS is_no_show,
                    CASE WHEN e.state = 'done'    THEN 1 ELSE 0 END AS is_done,
                    1                   AS entry_count
                FROM mediflow_queue_entry e
            )
        """ % self._table)
