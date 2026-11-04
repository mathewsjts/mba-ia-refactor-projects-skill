from datetime import datetime

from flask import jsonify


class SystemController:
    def health(self):
        return jsonify({'status': 'ok', 'timestamp': str(datetime.now())}), 200

    def index(self):
        return jsonify({'message': 'Task Manager API', 'version': '1.0'}), 200
