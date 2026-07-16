"""Stonelytics Studio Shell — The graphical shell of SRIE OS.
Every action passes through StudioService which wraps sdk.* calls."""
from flask import Flask, render_template, jsonify, request
from stonelytics.services import StudioService
import os

flask_app = Flask(__name__)
_SVC: StudioService | None = None


def get_svc() -> StudioService:
    global _SVC
    if _SVC is None:
        project = os.environ.get("STUDIO_PROJECT", ".")
        _SVC = StudioService(project)
    return _SVC


@flask_app.route("/")
def index():
    return render_template("studio.html")

@flask_app.route("/api/shell/identity")
def api_identity():
    return jsonify(get_svc().get_identity())

@flask_app.route("/api/shell/manifest")
def api_manifest():
    return jsonify(get_svc().get_manifest())

@flask_app.route("/api/shell/discover")
def api_discover():
    return jsonify(get_svc().discover())

@flask_app.route("/api/shell/indicators")
def api_indicators():
    return jsonify(get_svc().indicators())

@flask_app.route("/api/shell/twin")
def api_twin():
    return jsonify(get_svc().get_twin())

@flask_app.route("/api/shell/inspect")
def api_inspect():
    return jsonify(get_svc().inspect())

@flask_app.route("/api/shell/history")
def api_history():
    return jsonify(get_svc().history())

@flask_app.route("/api/shell/age")
def api_age():
    return jsonify(get_svc().get_age())

@flask_app.route("/api/shell/plan")
def api_plan():
    goal = request.args.get("goal", "Build MVP")
    return jsonify(get_svc().plan(goal))

@flask_app.route("/api/shell/orchestrate")
def api_orchestrate():
    goal = request.args.get("goal", "Build MVP")
    return jsonify(get_svc().orchestrate(goal))

@flask_app.route("/api/shell/capabilities")
def api_capabilities():
    return jsonify(get_svc().get_capabilities())

@flask_app.route("/api/shell/knowledge")
def api_knowledge():
    return jsonify(get_svc().get_knowledge())

@flask_app.route("/api/shell/knowledge/graph")
def api_knowledge_graph():
    svc = get_svc()
    twin = svc.get_twin()
    identity = svc.get_identity()
    caps = svc.get_capabilities()
    return jsonify({
        "nodes": [
            {"id": "PROJECT", "type": "root", "label": identity.get("name", "Project"), "state": "ACTIVE"},
            {"id": "IDENTITY", "type": "domain", "label": "Identity", "state": identity.get("state", "OK")},
            {"id": "RUNTIME", "type": "domain", "label": "Runtime", "state": svc.get_manifest().get("state", "?")},
            {"id": "TWIN", "type": "domain", "label": f"Digital Twin ({twin.get('nodes', 0)} nodes)", "state": "ACTIVE"},
            {"id": "CAPABILITIES", "type": "domain", "label": f"Capabilities ({len(caps)})", "state": "ACTIVE"},
        ],
        "relationships": [
            {"source": "PROJECT", "target": "IDENTITY", "type": "contains"},
            {"source": "PROJECT", "target": "RUNTIME", "type": "contains"},
            {"source": "PROJECT", "target": "TWIN", "type": "contains"},
            {"source": "PROJECT", "target": "CAPABILITIES", "type": "contains"},
        ],
    })

@flask_app.route("/api/shell/knowledge/patterns")
def api_knowledge_patterns():
    from srie.services.knowledge import KnowledgeEngine
    k = KnowledgeEngine(get_svc().path)
    return jsonify(k.list_patterns())

@flask_app.route("/api/shell/knowledge/cases")
def api_knowledge_cases():
    from srie.services.knowledge import KnowledgeEngine
    k = KnowledgeEngine(get_svc().path)
    return jsonify(k.list_cases())

@flask_app.route("/api/shell/deployments")
def api_deployments():
    svc = get_svc()
    targets = svc.list_targets()
    return jsonify({"targets": targets, "total": len(targets)})

@flask_app.route("/api/shell/deploy/run", methods=["POST"])
def api_deploy_run():
    data = request.get_json()
    return jsonify(get_svc().deploy(data.get("target_id", ""), data.get("version", "1.0.0")))

@flask_app.route("/api/shell/deploy/target", methods=["POST"])
def api_deploy_target():
    data = request.get_json()
    return jsonify(get_svc().register_target(data.get("name", "target"), data.get("env", "production"), data.get("url", "")))

@flask_app.route("/api/shell/deploy/rollback", methods=["POST"])
def api_deploy_rollback():
    from srie.services.deployment import Deployment
    data = request.get_json()
    d = Deployment(get_svc().path)
    return jsonify(d.rollback(data.get("target_id", "")))

@flask_app.route("/api/shell/deploy")
def api_deploy():
    return jsonify(get_svc().deploy())

@flask_app.route("/api/shell/targets")
def api_targets():
    return jsonify(get_svc().list_targets())

@flask_app.route("/api/shell/diagnose")
def api_diagnose():
    return jsonify(get_svc().diagnose())

@flask_app.route("/api/shell/repair")
def api_repair():
    return jsonify(get_svc().repair())

@flask_app.route("/api/shell/pause")
def api_pause():
    return jsonify(get_svc().pause())

@flask_app.route("/api/shell/resume")
def api_resume():
    return jsonify(get_svc().resume())

@flask_app.route("/api/shell/intention", methods=["POST"])
def api_intention():
    data = request.get_json()
    return jsonify(get_svc().execute_intention(data.get("intention", "")))

@flask_app.route("/api/shell/conductor", methods=["POST"])
def api_conductor():
    from stonelytics.conductor import Conductor
    data = request.get_json()
    c = Conductor(get_svc().path)
    result = c.execute(data.get("intention", ""))
    return jsonify(result)

@flask_app.route("/api/shell/workspace")
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


def app():
    flask_app.run(host="127.0.0.1", port=3000, debug=True)

if __name__ == "__main__":
    app()
