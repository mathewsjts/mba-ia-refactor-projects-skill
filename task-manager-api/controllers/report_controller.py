from flask import jsonify


class ReportController:
    def __init__(self, report_service):
        self._service = report_service

    def summary(self):
        return jsonify(self._service.summary()), 200

    def user_report(self, user_id):
        return jsonify(self._service.user_report(user_id)), 200
