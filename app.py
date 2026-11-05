import os
from flask import Flask, jsonify, render_template, request

from analyzer import analyze_code
from ai_review import ai_review

app = Flask(__name__)


@app.get('/')
def index():
    return render_template('index.html')


@app.post('/api/analyze')
def analyze():

    data = request.get_json(silent=True) or {}

    source = data.get('code', '')
    language = str(
        data.get('language', 'python')
    ).lower()

    include_ai = data.get('ai', False) is True

    if language not in {'python', 'java', 'c'}:
        return jsonify(
            error='Supported languages: Python, Java, C.'
        ), 400

    if not isinstance(source, str) or not source.strip():
        return jsonify(
            error='Please paste valid source code.'
        ), 400

    try:
        report = analyze_code(source, language)

        if not isinstance(report, dict):
            return jsonify(
                error='Invalid analyzer response.'
            ), 500

        if 'error' in report:
            return jsonify(report), 400

        if include_ai:
            report['ai_review'] = ai_review(
                source,
                report,
                language
            )

        return jsonify(report)

    except Exception as exc:
        app.logger.exception("Code analysis failed")

        return jsonify(
            error=f'Analysis failed: {type(exc).__name__}'
        ), 500


if __name__ == '__main__':
    app.run(
        debug=os.getenv('FLASK_DEBUG', '0') == '1'
    )