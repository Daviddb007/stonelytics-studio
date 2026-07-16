"""The Conductor — orchestrates intentions into executed workflows.
Decides which modules to activate, which capabilities to use,
and how to sequence work. Reports progress at every step."""
from srie import SDK
from pathlib import Path
from datetime import datetime, timezone
import json


class Conductor:

    def __init__(self, project_path: Path):
        self._path = project_path
        self._sdk = SDK(str(project_path))
        self._sdk.init()

    def execute(self, intention: str) -> dict:
        start = datetime.now(timezone.utc)
        steps = []
        errors = []

        def step(name, status="running", detail=""):
            s = {"name": name, "status": status, "detail": detail, "ts": datetime.now(timezone.utc).isoformat()}
            steps.append(s)
            return s

        try:
            step("Interpreting intention", "running", f"Parsing: {intention[:60]}...")
            plan_type = self._classify_intention(intention)

            if plan_type == "build":
                step("Planning architecture", "running", "Inferring workflow from goal...")
                import importlib.util
                import srie
                srie_root = Path(srie.__file__).parent
                engine_path = srie_root / "modules" / "planner" / "engine.py"
                spec = importlib.util.spec_from_file_location("planner_engine", engine_path)
                PlannerEngine = None
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    PlannerEngine = mod.PlannerEngine
                if not PlannerEngine:
                    raise ImportError(f"Planner module not found")
                planner = PlannerEngine(self._path)
                plan = planner.plan_from_goal(intention)

                step("Matching capabilities", "running", f"{plan['total_steps']} steps identified")
                from srie.kernel.capability import CapabilityEngine
                caps = CapabilityEngine(self._path)
                assignments = caps.match_workflow(plan["steps"])
                cost = caps.estimated_cost(plan["steps"])
                gaps = caps.resource_gap(plan["steps"], ["filesystem", "git", "digital_twin"])

                step("Allocating resources", "running" if not gaps else "blocked", f"Cost: {cost}, Resources: {len(assignments)} capabilities matched")
                if gaps:
                    step("Resource gaps", "warning", f"Missing: {', '.join(gaps)}")

                step("Creating execution", "running", "Starting orchestrated workflow...")
                result = planner.execute_plan(plan)
                step("Execution created", "complete", f"ID: {result['execution_id']}, {result['steps']} steps")

                step("Discovering project", "running")
                disc = self._sdk.discover()
                step("Discovery complete", "complete", f"{len(disc.languages)} languages, {disc.files.total if disc.files else 0} files")

                step("Calculating indicators", "running")
                ind = self._sdk.indicators()
                step("Indicators complete", "complete", f"Score: {ind.srie_score:.1f}, Maturity: {ind.maturity_level}")

                step("Finalizing", "complete", f"Execution {result['execution_id']} is RUNNING")

            elif plan_type == "analyze":
                step("Running discovery", "running")
                disc = self._sdk.discover()
                step("Discovery complete", "complete", f"{len(disc.languages)} languages, confidence {disc.confidence:.2f}")

                step("Calculating indicators", "running")
                ind = self._sdk.indicators()
                step("Indicators complete", "complete", f"SRIE Score: {ind.srie_score:.1f}, Level: {ind.maturity_level}")

                step("Checking runtime health", "running")
                manifest = self._sdk.manifest()
                state = manifest.state if manifest else "unknown"
                step("Health check complete", "complete", f"Runtime: {state}")

            elif plan_type == "deploy":
                from srie.services.deployment import Deployment
                d = Deployment(self._path)
                targets = d.list_targets()
                if targets:
                    step("Deploying", "running", f"Target: {targets[0]['name']}")
                    dep = d.deploy(targets[0]["id"], "1.0.0")
                    step("Deployed", "complete", f"Version 1.0.0 to {targets[0]['name']}")
                else:
                    step("No targets", "blocked", "Register a target with 'srie ops target' first")

            elif plan_type == "repair":
                from srie.services.repair import RepairEngine
                r = RepairEngine(self._path)
                issues = r.diagnose()
                step("Diagnosing", "running" if issues else "complete", f"{len(issues)} issues found")
                if issues:
                    results = r.auto_repair_all()
                    fixed = sum(1 for x in results if x["applied"])
                    step("Repairs applied", "complete", f"{fixed}/{len(results)} auto-fixed")

            else:
                step("Unknown intention", "error", f"No plan for: {intention[:80]}")

        except Exception as e:
            step("Error", "error", str(e))
            errors.append(str(e))

        duration = int((datetime.now(timezone.utc) - start).total_seconds())
        return {
            "intention": intention,
            "duration_seconds": duration,
            "steps": steps,
            "errors": errors,
            "status": "complete" if not errors else "failed",
        }

    def _classify_intention(self, text: str) -> str:
        t = text.lower()
        if any(w in t for w in ["construir", "build", "mvp", "crear", "hacer", "generar", "develop"]):
            return "build"
        if any(w in t for w in ["analizar", "analyze", "indicador", "health", "status", "evaluar"]):
            return "analyze"
        if any(w in t for w in ["desplegar", "deploy", "publicar", "release"]):
            return "deploy"
        if any(w in t for w in ["reparar", "repair", "fix", "arreglar", "error"]):
            return "repair"
        return "analyze"
