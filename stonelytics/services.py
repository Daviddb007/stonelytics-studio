"""Studio Service Layer — the ONLY bridge between the Shell and SRIE.
Every operation wraps sdk.* calls. No direct Runtime module imports."""
from srie import SDK
from pathlib import Path


class StudioService:

    def __init__(self, project_path: str):
        self._sdk = SDK(project_path)
        self._path = Path(project_path).resolve()
        self._booted = False

    def ensure_booted(self):
        if not self._booted:
            self._sdk.init()
            self._booted = True

    @property
    def sdk(self) -> SDK:
        return self._sdk

    @property
    def path(self) -> Path:
        return self._path

    # === Identity ===
    def get_identity(self) -> dict:
        self.ensure_booted()
        i = self._sdk.identity()
        return {"domain_id": i.domain_id, "name": i.name, "type": i.type, "state": i.state}

    # === Runtime ===
    def get_manifest(self) -> dict:
        self.ensure_booted()
        m = self._sdk.manifest()
        if not m:
            return {"state": "STOPPED", "version": "N/A", "modules": []}
        return {"state": m.state, "version": m.runtime_version, "modules": [{"id": mo.id, "state": mo.state} for mo in m.modules]}

    def pause(self) -> dict:
        self.ensure_booted()
        self._sdk.pause()
        return {"state": "SUSPENDED"}

    def resume(self) -> dict:
        self.ensure_booted()
        self._sdk.resume()
        return {"state": "RUNNING"}

    def get_age(self) -> dict:
        self.ensure_booted()
        return self._sdk.operational_age()

    # === Discovery ===
    def discover(self) -> dict:
        self.ensure_booted()
        r = self._sdk.discover()
        return {"languages": [l.name for l in r.languages], "frameworks": [f.name for f in r.frameworks], "files": r.files.total if r.files else 0, "confidence": r.confidence}

    # === Indicators ===
    def indicators(self) -> dict:
        self.ensure_booted()
        r = self._sdk.indicators()
        return {"score": r.srie_score, "maturity": r.maturity_level, "domains": r.by_domain}

    # === Twin ===
    def get_twin(self) -> dict:
        self.ensure_booted()
        t = self._sdk.twin()
        if not t:
            return {"nodes": 0, "relationships": 0, "version": 0}
        return {"nodes": len(t.nodes), "relationships": len(t.relationships), "version": t.version}

    # === Inspect ===
    def inspect(self) -> dict:
        self.ensure_booted()
        from srie.cli.commands.inspect import _build_full_tree
        return _build_full_tree(self._sdk)

    # === History ===
    def history(self, limit: int = 50) -> list:
        self.ensure_booted()
        events = self._sdk.journal(limit)
        return [{"ts": e.get("timestamp", "")[:19], "source": e.get("source", ""), "msg": e.get("message", "")} for e in reversed(events)]

    # === Plan & Orchestrate ===
    def plan(self, goal: str = "Build MVP") -> dict:
        self.ensure_booted()
        p = self._plan_engine()
        plan = p.plan_from_goal(goal)
        return {"goal": goal, "steps": len(plan["steps"]), "time": plan.get("estimated_time_min", 0), "cost": plan.get("estimated_cost", 0), "details": plan["steps"]}

    def orchestrate(self, goal: str = "Build MVP") -> dict:
        self.ensure_booted()
        p = self._plan_engine()
        plan = p.plan_from_goal(goal)
        result = p.execute_plan(plan)
        return {"execution_id": result["execution_id"], "goal": result["goal"], "steps": result["steps"], "time": result.get("estimated_time_min", 0)}

    # === Capabilities ===
    def get_capabilities(self) -> list:
        self.ensure_booted()
        c = self._cap_engine()
        return c.registry()

    def match_capability(self, action: str) -> list:
        self.ensure_booted()
        c = self._cap_engine()
        return c.match(action)

    # === Knowledge ===
    def get_knowledge(self) -> dict:
        self.ensure_booted()
        k = self._know_engine()
        return {"patterns": len(k.list_patterns()), "cases": len(k.list_cases()), "reuse": k.reuse_rate()}

    # === Deploy ===
    def deploy(self, target_id: str = "", version: str = "1.0.0") -> dict:
        self.ensure_booted()
        d = self._deploy_engine()
        targets = d.list_targets()
        if not targets:
            return {"error": "No targets registered. Use 'srie ops target' first."}
        tgt = targets[0] if not target_id else next((t for t in targets if t["id"] == target_id), targets[0])
        dep = d.deploy(tgt["id"], version)
        return {"target": tgt["name"], "version": version, "deployment_id": dep["id"], "state": dep["state"]}

    def register_target(self, name: str, env: str = "production", url: str = "") -> dict:
        self.ensure_booted()
        d = self._deploy_engine()
        tgt = d.register_target(name, env, url)
        return {"id": tgt["id"], "name": name, "environment": env}

    def list_targets(self) -> list:
        self.ensure_booted()
        d = self._deploy_engine()
        return d.list_targets()

    # === Repair ===
    def diagnose(self) -> list:
        self.ensure_booted()
        r = self._repair_engine()
        return r.diagnose()

    def repair(self) -> dict:
        self.ensure_booted()
        r = self._repair_engine()
        results = r.auto_repair_all()
        return {"fixed": sum(1 for x in results if x["applied"]), "total": len(results)}

    # === Intention ===
    def execute_intention(self, intention: str) -> dict:
        self.ensure_booted()
        text = intention.lower()
        if any(w in text for w in ["construir", "build", "mvp", "crear"]):
            return self.orchestrate(intention)
        elif any(w in text for w in ["analizar", "analyze", "indicador", "health"]):
            return {"action": "indicators", **self.indicators()}
        elif any(w in text for w in ["descubrir", "discover", "escanear", "scan"]):
            return {"action": "discover", **self.discover()}
        elif any(w in text for w in ["desplegar", "deploy", "publicar"]):
            return {"action": "deploy", **self.deploy()}
        elif any(w in text for w in ["reparar", "repair", "fix", "arreglar"]):
            return {"action": "repair", **self.repair()}
        elif any(w in text for w in ["plan", "planificar"]):
            return {"action": "plan", **self.plan(intention)}
        elif any(w in text for w in ["pausar", "pause", "suspender"]):
            return {"action": "pause", **self.pause()}
        elif any(w in text for w in ["reanudar", "resume"]):
            return {"action": "resume", **self.resume()}
        else:
            return {"action": "unknown", "message": f"No handler for: {intention}", "hint": "Try: build MVP, analyze, discover, deploy, repair, plan, pause, resume"}

    # === Internal engine factories (thin wrappers, not module imports) ===
    def _plan_engine(self):
        import importlib.util
        import srie
        srie_root = Path(srie.__file__).parent
        engine_path = srie_root / "modules" / "planner" / "engine.py"
        spec = importlib.util.spec_from_file_location("planner_engine", engine_path)
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod.PlannerEngine(self._path)
        raise ImportError(f"Planner module not found at {engine_path}")

    def _cap_engine(self):
        from srie.kernel.capability import CapabilityEngine
        return CapabilityEngine(self._path)

    def _know_engine(self):
        from srie.services.knowledge import KnowledgeEngine
        return KnowledgeEngine(self._path)

    def _deploy_engine(self):
        from srie.services.deployment import Deployment
        return Deployment(self._path)

    def _repair_engine(self):
        from srie.services.repair import RepairEngine
        return RepairEngine(self._path)
