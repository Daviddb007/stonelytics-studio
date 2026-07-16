"""Stonelytics Studio Shell — The graphical shell of SRIE OS.
Every action passes through StudioService which wraps sdk.* calls."""
from flask import Flask, render_template, jsonify, request
from stonelytics.services import StudioService
import os

app = Flask(__name__)
_SVC: StudioService | None = None


def get_svc() -> StudioService:
    global _SVC
    if _SVC is None:
        project = os.environ.get("STUDIO_PROJECT", ".")
        _SVC = StudioService(project)
    return _SVC


@app.route("/")
def index():
    return render_template("studio.html")

@app.route("/api/shell/identity")
def api_identity():
    return jsonify(get_svc().get_identity())

@app.route("/api/shell/manifest")
def api_manifest():
    return jsonify(get_svc().get_manifest())

@app.route("/api/shell/discover")
def api_discover():
    return jsonify(get_svc().discover())

@app.route("/api/shell/indicators")
def api_indicators():
    return jsonify(get_svc().indicators())

@app.route("/api/shell/twin")
def api_twin():
    return jsonify(get_svc().get_twin())

@app.route("/api/shell/inspect")
def api_inspect():
    return jsonify(get_svc().inspect())

@app.route("/api/shell/history")
def api_history():
    return jsonify(get_svc().history())

@app.route("/api/shell/age")
def api_age():
    return jsonify(get_svc().get_age())

@app.route("/api/shell/plan")
def api_plan():
    goal = request.args.get("goal", "Build MVP")
    return jsonify(get_svc().plan(goal))

@app.route("/api/shell/orchestrate")
def api_orchestrate():
    goal = request.args.get("goal", "Build MVP")
    return jsonify(get_svc().orchestrate(goal))

@app.route("/api/shell/capabilities")
def api_capabilities():
    return jsonify(get_svc().get_capabilities())

@app.route("/api/shell/knowledge")
def api_knowledge():
    return jsonify(get_svc().get_knowledge())

@app.route("/api/shell/deploy")
def api_deploy():
    return jsonify(get_svc().deploy())

@app.route("/api/shell/targets")
def api_targets():
    return jsonify(get_svc().list_targets())

@app.route("/api/shell/diagnose")
def api_diagnose():
    return jsonify(get_svc().diagnose())

@app.route("/api/shell/repair")
def api_repair():
    return jsonify(get_svc().repair())

@app.route("/api/shell/pause")
def api_pause():
    return jsonify(get_svc().pause())

@app.route("/api/shell/resume")
def api_resume():
    return jsonify(get_svc().resume())

@app.route("/api/shell/intention", methods=["POST"])
def api_intention():
    data = request.get_json()
    return jsonify(get_svc().execute_intention(data.get("intention", "")))

@app.route("/api/shell/workspace")
def api_workspace():
    svc = get_svc()
    identity = svc.get_identity()
    manifest = svc.get_manifest()
    twin = svc.get_twin()
    indicators = svc.indicators()
    age = svc.get_age()
    return jsonify({
        "identity": identity,
        "manifest": manifest,
        "twin": twin,
        "indicators": indicators,
        "age": age,
    })


def main():
    app.run(host="127.0.0.1", port=3000, debug=True)

if __name__ == "__main__":
    main()
