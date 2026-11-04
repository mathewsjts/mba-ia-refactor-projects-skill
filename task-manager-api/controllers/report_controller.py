from flask import g, jsonify

from routes.serializers import serialize_summary, serialize_user_report


class ReportController:
    def __init__(self, report_service):
        self._service = report_service

    def summary(self):
        return jsonify(serialize_summary(self._service.summary())), 200

    def user_report(self, user_id):
        user, statistics = self._service.user_report(g.user, user_id)
        return jsonify(serialize_user_report(user, statistics)), 200
