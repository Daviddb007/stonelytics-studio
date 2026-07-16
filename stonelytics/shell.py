"""Stonelytics Studio — IDE for Cognitive Engineering.
Every action passes through the SRIE SDK. No direct module access."""
from flask import Flask, render_template, jsonify, request
from srie import SDK
from pathlib import Path
import os

app = Flask(__name__)

_SDK: SDK | None = None


def get_sdk() -> SDK:
    global _SDK
    if _SDK is None:
        project = os.environ.get("STUDIO_PROJECT", ".")
        _SDK = SDK(project)
        _SDK.init()
    return _SDK


@app.route("/")
def index():
    return render_template("studio.html")


@app.route("/api/sdk/identity")
def api_identity():
    sdk = get_sdk()
    i = sdk.identity()
    return jsonify({"domain_id": i.domain_id, "name": i.name, "type": i.type, "state": i.state})

@app.route("/api/sdk/manifest")
def api_manifest():
    sdk = get_sdk()
    m = sdk.manifest()
    if not m:
        return jsonify({"error": "Not initialized"})
    return jsonify({"state": m.state, "version": m.runtime_version, "modules": [{"id": mo.id, "state": mo.state} for mo in m.modules]})

@app.route("/api/sdk/discover")
def api_discover():
    sdk = get_sdk()
    r = sdk.discover()
    return jsonify({"languages": [l.name for l in r.languages], "frameworks": [f.name for f in r.frameworks], "files": r.files.total if r.files else 0, "confidence": r.confidence})

@app.route("/api/sdk/indicators")
def api_indicators():
    sdk = get_sdk()
    r = sdk.indicators()
    return jsonify({"score": r.srie_score, "maturity": r.maturity_level, "domains": r.by_domain})

@app.route("/api/sdk/twin")
def api_twin():
    sdk = get_sdk()
    t = sdk.twin()
    if not t:
        return jsonify({"nodes": 0})
    return jsonify({"nodes": len(t.nodes), "relationships": len(t.relationships), "version": t.version})

@app.route("/api/sdk/inspect")
def api_inspect():
    sdk = get_sdk()
    from srie.cli.commands.inspect import _build_full_tree
    return jsonify(_build_full_tree(sdk))

@app.route("/api/sdk/why")
def api_why():
    sdk = get_sdk()
    from srie.cli.commands.inspect import cmd_why
    import io, sys
    buf = io.StringIO()
    sys.stdout = buf
    try:
        cmd_why(str(sdk.path))
    finally:
        sys.stdout = sys.__stdout__
    return jsonify({"analysis": buf.getvalue()})

@app.route("/api/sdk/history")
def api_history():
    sdk = get_sdk()
    events = sdk.journal(50)
    return jsonify([{"ts": e.get("timestamp", "")[:19], "source": e.get("source", ""), "msg": e.get("message", "")} for e in reversed(events)])

@app.route("/api/sdk/plan")
def api_plan():
    sdk = get_sdk()
    goal = request.args.get("goal", "Build MVP")
    from srie.modules.planner.planner import PlannerEngine
    p = PlannerEngine(sdk.path)
    plan = p.plan_from_goal(goal)
    return jsonify({"goal": goal, "steps": len(plan["steps"]), "time": plan.get("estimated_time_min", 0), "cost": plan.get("estimated_cost", 0)})

@app.route("/api/sdk/execute")
def api_execute():
    sdk = get_sdk()
    goal = request.args.get("goal", "Build MVP")
    from srie.modules.planner.planner import PlannerEngine
    p = PlannerEngine(sdk.path)
    plan = p.plan_from_goal(goal)
    result = p.execute_plan(plan)
    return jsonify({"execution_id": result["execution_id"], "goal": result["goal"], "steps": result["steps"]})

@app.route("/api/sdk/capabilities")
def api_capabilities():
    sdk = get_sdk()
    from srie.kernel.capability import CapabilityEngine
    c = CapabilityEngine(sdk.path)
    return jsonify(c.registry())

@app.route("/api/sdk/knowledge")
def api_knowledge():
    sdk = get_sdk()
    from srie.services.knowledge import KnowledgeEngine
    k = KnowledgeEngine(sdk.path)
    return jsonify({"patterns": len(k.list_patterns()), "cases": len(k.list_cases()), "reuse": k.reuse_rate()})

@app.route("/api/sdk/execute_intention", methods=["POST"])
def api_execute_intention():
    sdk = get_sdk()
    data = request.get_json()
    intention = data.get("intention", "").lower()

    if "construir" in intention or "build" in intention or "mvp" in intention:
        from srie.modules.planner.planner import PlannerEngine
        p = PlannerEngine(sdk.path)
        plan = p.plan_from_goal(intention)
        result = p.execute_plan(plan)
        return jsonify({"action": "orchestrated", "execution_id": result["execution_id"], "goal": intention, "steps": result["steps"]})
    elif "analizar" in intention or "analyze" in intention or "indicador" in intention:
        r = sdk.indicators()
        return jsonify({"action": "indicators", "score": r.srie_score, "maturity": r.maturity_level})
    elif "descubrir" in intention or "discover" in intention or "escanear" in intention:
        r = sdk.discover()
        return jsonify({"action": "discover", "languages": [l.name for l in r.languages], "files": r.files.total if r.files else 0})
    elif "desplegar" in intention or "deploy" in intention:
        from srie.services.deployment import Deployment
        d = Deployment(sdk.path)
        targets = d.list_targets()
        if targets:
            dep = d.deploy(targets[0]["id"], "1.0.0")
            return jsonify({"action": "deploy", "target": targets[0]["name"], "version": "1.0.0"})
        return jsonify({"action": "deploy", "error": "No targets registered"})
    elif "reparar" in intention or "repair" in intention or "fix" in intention:
        from srie.services.repair import RepairEngine
        r = RepairEngine(sdk.path)
        results = r.auto_repair_all()
        return jsonify({"action": "repair", "fixed": sum(1 for x in results if x["applied"])})
    else:
        return jsonify({"action": "unknown", "message": f"No handler for: {intention}", "hint": "Try: build MVP, analyze project, discover, deploy, repair"})


def main():
    app.run(host="127.0.0.1", port=3000, debug=True)

if __name__ == "__main__":
    main()
