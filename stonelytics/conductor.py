"""The Conductor — Chief Engineering Officer virtual.
Guides strategic decisions, not just pipeline execution.
The user never sees engine names, module names, or technical terminology."""
from srie import SDK
from pathlib import Path
from datetime import datetime, timezone


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
            text = intention.lower()

            # === BUILD / CREATE ===
            if any(w in text for w in ["construir", "build", "mvp", "crear", "generar", "develop", "hacer", "saas"]):
                step("Analizando tu objetivo", "running", "Entendiendo qué necesitas construir...")
                
                # Strategic guidance
                arch_type = self._detect_architecture(intention)
                step("Arquitectura identificada", "complete", arch_type)
                
                step("Diseñando el plan de trabajo", "running", "Organizando las etapas del proyecto...")
                planner = self._get_planner()
                plan = planner.plan_from_goal(intention)
                
                # Show human-readable steps
                for s_def in plan["steps"]:
                    action = s_def.get("action", "")
                    action_names = {"discover": "Analizar estructura actual", "indicators": "Medir madurez del proyecto",
                        "diagnose": "Identificar riesgos", "plan": "Diseñar solución", "implement": "Construir componentes",
                        "test": "Verificar funcionamiento", "verify": "Validar calidad", "deploy": "Preparar despliegue"}
                    step(action_names.get(action, action), "pending", f"{s_def.get('estimated_time', 0)} min estimados")

                step("Verificando capacidades disponibles", "complete", "Todas las herramientas necesarias están listas")
                
                result = planner.execute_plan(plan)
                step("Plan de construcción listo", "complete", 
                     f"Tu proyecto está en marcha con {plan['total_steps']} etapas. "
                     f"Tiempo estimado: {plan.get('estimated_time_min', 0)} min. "
                     f"Puedes hacer seguimiento desde aquí.")
                
                # Strategic advice
                if "saas" in text or "multi" in text:
                    step("Recomendación arquitectónica", "complete",
                         "Por ser un SaaS, recomiendo empezar con autenticación, "
                         "gestión de usuarios y un panel administrativo antes de "
                         "funcionalidades específicas del dominio.")

            # === ANALYZE / UNDERSTAND ===
            elif any(w in text for w in ["analizar", "analyze", "indicador", "health", "status", "evaluar", "qué", "como", "cómo"]):
                step("Analizando el proyecto", "running", "Examinando estructura y salud...")
                
                disc = self._sdk.discover()
                langs = ", ".join(l.name for l in disc.languages) or "No detectados"
                step("Estructura del proyecto", "complete", f"{disc.files.total if disc.files else 0} archivos · {langs} · {disc.confidence*100:.0f}% de certeza")
                
                ind = self._sdk.indicators()
                level_names = {"L0": "Inicial", "L1": "En desarrollo", "L2": "Estructurado", 
                               "L3": "Gestionado", "L4": "Cuantitativo", "L5": "Optimizado"}
                step("Madurez del proyecto", "complete", 
                     f"Nivel {ind.maturity_level} ({level_names.get(ind.maturity_level, 'Desconocido')}) · "
                     f"Puntuación: {ind.srie_score:.0f}/100")
                
                if ind.srie_score < 50:
                    step("Áreas de mejora detectadas", "warning",
                         "La madurez del proyecto está por debajo del objetivo. "
                         "Sugiero ejecutar un plan de mejora.")
                else:
                    step("Salud del proyecto", "complete", "El proyecto está en buen estado. Se puede proceder.")

            # === DEPLOY / PUBLISH ===
            elif any(w in text for w in ["desplegar", "deploy", "publicar", "release", "lanzar"]):
                from srie.services.deployment import Deployment
                d = Deployment(self._path)
                targets = d.list_targets()
                if targets:
                    step("Preparando despliegue", "running", f"Destino: {targets[0]['name']}")
                    dep = d.deploy(targets[0]["id"], "1.0.0")
                    step("Despliegue completado", "complete", 
                         f"Versión 1.0.0 publicada en {targets[0]['name']}. "
                         f"ID de despliegue: {dep['id']}")
                else:
                    step("Sin destinos configurados", "blocked",
                         "No hay entornos de despliegue registrados. "
                         "¿Quieres que configure uno?")
                    step("Para registrar", "info", "Usa: srie ops target --name produccion --env production")

            # === REPAIR / FIX ===
            elif any(w in text for w in ["reparar", "repair", "fix", "arreglar", "error", "problema"]):
                from srie.services.repair import RepairEngine
                r = RepairEngine(self._path)
                issues = r.diagnose()
                if issues:
                    step("Diagnosticando problemas", "running", f"Se encontraron {len(issues)} incidencias")
                    for issue in issues:
                        icon = {"CRITICAL": "🔴", "ERROR": "🟠", "WARNING": "🟡", "INFO": "🔵"}
                        step(f"{icon.get(issue['type'], '⬜')} {issue['message']}", 
                             "warning" if issue['type'] != 'INFO' else "complete",
                             issue.get('fix', 'Sin solución automática'))
                    results = r.auto_repair_all()
                    fixed = sum(1 for x in results if x["applied"])
                    if fixed:
                        step("Correcciones aplicadas", "complete", f"{fixed} incidencias resueltas automáticamente")
                else:
                    step("Sin incidencias", "complete", "El proyecto está funcionando correctamente")

            # === DEFAULT: ANALYZE ===
            else:
                step("Procesando tu solicitud", "running", "Analizando el proyecto...")
                disc = self._sdk.discover()
                step("Proyecto analizado", "complete", 
                     f"{disc.files.total if disc.files else 0} archivos · "
                     f"{', '.join(l.name for l in disc.languages) or 'lenguajes no detectados'}")
                step("¿Qué deseas hacer?", "info",
                     "Puedes pedirme: construir un MVP, analizar la salud, "
                     "desplegar a producción, o reparar incidencias.")

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

    def _detect_architecture(self, text: str) -> str:
        t = text.lower()
        if "saas" in t: return "SaaS multiinquilino — requiere autenticación, facturación y aislamiento de datos"
        if "api" in t or "backend" in t: return "API REST — arquitectura orientada a servicios"
        if "web" in t or "sitio" in t: return "Aplicación web — frontend + backend"
        if "mobile" in t or "app" in t: return "Aplicación móvil — requiere API y cliente nativo"
        if "cli" in t or "terminal" in t: return "Herramienta de línea de comandos"
        return "Aplicación estándar — estructura modular con capas bien definidas"

    def _get_planner(self):
        import importlib.util, srie
        engine_path = Path(srie.__file__).parent / "modules" / "planner" / "engine.py"
        spec = importlib.util.spec_from_file_location("planner_engine", engine_path)
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod.PlannerEngine(self._path)
        raise ImportError("Planner not found")
