"""
JADWA Report Generation Pipeline
DAG-based multi-agent orchestration via Celery.

Execution order:
  Tier 1 (sequential): IntakeValidation → SectorRouter
  Tier 2 (parallel):   Market + Legal + HR + [Franchise|RealEstate] (conditional)
  Tier 2b (depends):   Financial (needs Market + HR) + Competitive
  Tier 2c:             Vision2030 + RiskAssessment (needs all Tier 2)
  Tier 3 (sequential): Charts → Compiler → QualityReview → PDF
"""

import concurrent.futures
from datetime import datetime, timedelta
from typing import Optional

from app.tasks.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.report import ReportRun, ReportOutput
from app.models.project import Project


def _extract_essentials(result: dict, max_chars: int = 1500) -> dict:
    """
    Extract essential fields from an agent result, dropping raw_output
    and truncating to max_chars to keep downstream context small.
    """
    if not result or not isinstance(result, dict):
        return result
    # Drop raw_output (the largest field), keep structured keys
    slim = {k: v for k, v in result.items() if k != "raw_output"}
    # If stripping raw_output left nothing useful, fall back to truncated raw
    if not slim or (len(slim) == 1 and "agent" in slim):
        raw = result.get("raw_output", "")
        slim["summary"] = raw[:max_chars] + ("..." if len(raw) > max_chars else "")
        slim["agent"] = result.get("agent", "")
    import json as _json

    serialized = _json.dumps(slim, ensure_ascii=False)
    if len(serialized) > max_chars:
        # Brute-force truncate the whole dict serialization
        slim = {"summary": serialized[:max_chars] + "... [truncated]"}
    return slim


def _update_run(
    db,
    run_id: str,
    status: str = None,
    step: str = None,
    progress: int = None,
    error: str = None,
):
    run = db.query(ReportRun).filter(ReportRun.id == run_id).first()
    if not run:
        return
    if status:
        run.status = status
    if step:
        run.current_step = step
    if progress is not None:
        run.progress_percent = progress
    if error:
        run.error_message = error
    db.commit()


@celery_app.task(bind=True, name="pipeline.run_report_pipeline", max_retries=1)
def run_report_pipeline(self, run_id: str, language: str = "ar"):
    """
    Main Celery task: orchestrates the full 15-agent pipeline.
    """
    db = SessionLocal()
    try:
        run = db.query(ReportRun).filter(ReportRun.id == run_id).first()
        if not run:
            return {"error": "Run not found"}

        project = db.query(Project).filter(Project.id == run.project_id).first()
        if not project:
            _update_run(db, run_id, status="failed", error="Project not found")
            return

        intake = project.intake_data
        sector = project.sector

        run.started_at = datetime.utcnow()
        _update_run(db, run_id, status="running", step="بدء التحليل...", progress=2)

        # ── TIER 1: INTAKE ──────────────────────────────────────────────
        _update_run(db, run_id, step="التحقق من البيانات المدخلة...", progress=5)
        from app.agents.intake_validation_agent import IntakeValidationAgent

        intake_agent = IntakeValidationAgent(db=db, run_id=run_id)
        validated = intake_agent.run(
            {"intake": intake, "sector": sector, "language": language}
        )

        if validated.get("completeness_score", 100) < 50:
            _update_run(
                db,
                run_id,
                status="failed",
                error="Intake data too incomplete (score < 50)",
            )
            return

        _update_run(db, run_id, step="تحديد مسار التقرير...", progress=8)
        from app.agents.sector_router_agent import SectorRouterAgent

        router = SectorRouterAgent(db=db, run_id=run_id)
        routing = router.run({"validated_context": validated, "sector": sector})

        # Build project context passed to all agents
        ctx = {
            "sector": sector,
            "language": language,
            "intake": intake,
            "validated": validated,
            "routing": routing,
        }

        # ── TIER 2: PARALLEL ANALYSIS ───────────────────────────────────
        _update_run(db, run_id, step="تحليل السوق والبيئة التنظيمية...", progress=12)

        from app.agents.market.orchestrator import (
            MarketOrchestrator as MarketResearchAgent,
        )
        from app.agents.legal.orchestrator import (
            LegalOrchestrator as LegalRegulatoryAgent,
        )
        from app.agents.hr.orchestrator import HROrchestrator as HRSaudizationAgent

        market_result = legal_result = hr_result = {}
        franchise_result = real_estate_result = {}

        def run_market():
            return MarketResearchAgent(db=db, run_id=run_id).run(ctx)

        def run_legal():
            return LegalRegulatoryAgent(db=db, run_id=run_id).run(ctx)

        def run_hr():
            return HRSaudizationAgent(db=db, run_id=run_id).run(ctx)

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures = {
                "market": executor.submit(run_market),
                "legal": executor.submit(run_legal),
                "hr": executor.submit(run_hr),
            }

            # Add sector-specific agents
            if sector == "franchise":
                from app.agents.franchise.orchestrator import (
                    FranchiseOrchestrator as FranchiseAgent,
                )

                futures["franchise"] = executor.submit(
                    lambda: FranchiseAgent(db=db, run_id=run_id).run(ctx)
                )
            elif sector == "real_estate":
                from app.agents.real_estate_agent import RealEstateAgent

                futures["real_estate"] = executor.submit(
                    lambda: RealEstateAgent(db=db, run_id=run_id).run(ctx)
                )

            for key, future in futures.items():
                try:
                    result = future.result(timeout=300)
                    if key == "market":
                        market_result = result
                    elif key == "legal":
                        legal_result = result
                    elif key == "hr":
                        hr_result = result
                    elif key == "franchise":
                        franchise_result = result
                    elif key == "real_estate":
                        real_estate_result = result
                except Exception as e:
                    _update_run(
                        db, run_id, step=f"تحذير: فشل وكيل {key}", progress=None
                    )

        _update_run(
            db, run_id, step="بناء النموذج المالي وتحليل المنافسين...", progress=35
        )

        # ── TIER 2b: FINANCIAL + COMPETITIVE (depend on market + hr) ──
        ctx_2b = {
            **ctx,
            "market": _extract_essentials(market_result),
            "hr": _extract_essentials(hr_result),
            "legal": _extract_essentials(legal_result),
        }

        from app.agents.financial.orchestrator import (
            FinancialOrchestrator as FinancialModelingAgent,
        )
        from app.agents.competitive_analysis_agent import CompetitiveAnalysisAgent

        financial_result = competitive_result = {}

        def run_financial():
            return FinancialModelingAgent(db=db, run_id=run_id).run(ctx_2b)

        def run_competitive():
            return CompetitiveAnalysisAgent(db=db, run_id=run_id).run(ctx_2b)

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            f_fin = executor.submit(run_financial)
            f_comp = executor.submit(run_competitive)
            try:
                financial_result = f_fin.result(timeout=300)
            except Exception:
                pass
            try:
                competitive_result = f_comp.result(timeout=300)
            except Exception:
                pass

        _update_run(
            db, run_id, step="تقييم التوافق مع رؤية 2030 وتحليل المخاطر...", progress=55
        )

        # ── TIER 2c: VISION2030 + RISK (need all prior outputs) ──
        ctx_2c = {
            **ctx_2b,
            "financial": _extract_essentials(financial_result),
            "competitive": _extract_essentials(competitive_result),
            "franchise": _extract_essentials(franchise_result),
            "real_estate": _extract_essentials(real_estate_result),
        }

        from app.agents.vision.orchestrator import VisionOrchestrator as Vision2030Agent
        from app.agents.risk_assessment_agent import RiskAssessmentAgent

        vision_result = risk_result = {}

        def run_vision():
            return Vision2030Agent(db=db, run_id=run_id).run(ctx_2c)

        def run_risk():
            return RiskAssessmentAgent(db=db, run_id=run_id).run(ctx_2c)

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            f_vis = executor.submit(run_vision)
            f_risk = executor.submit(run_risk)
            try:
                vision_result = f_vis.result(timeout=300)
            except Exception:
                pass
            try:
                risk_result = f_risk.result(timeout=300)
            except Exception:
                pass

        _update_run(db, run_id, step="إنشاء الرسوم البيانية...", progress=68)

        # ── TIER 3: SYNTHESIS ──────────────────────────────────────────
        all_results = {
            "market": market_result,
            "legal": legal_result,
            "hr": hr_result,
            "financial": financial_result,
            "competitive": competitive_result,
            "vision2030": vision_result,
            "risk": risk_result,
            "franchise": franchise_result,
            "real_estate": real_estate_result,
        }

        from app.agents.chart_generation_agent import ChartGenerationAgent

        chart_agent = ChartGenerationAgent(db=db, run_id=run_id)
        chart_result = chart_agent.run(all_results)

        _update_run(db, run_id, step="تجميع التقرير النهائي...", progress=75)

        from app.agents.report_compiler_agent import ReportCompilerAgent

        compiler = ReportCompilerAgent(db=db, run_id=run_id)
        report_doc = compiler.run(
            {
                **all_results,
                "charts": chart_result,
                "intake": intake,
                "sector": sector,
                "language": language,
            }
        )

        _update_run(db, run_id, step="مراجعة جودة التقرير...", progress=85)

        from app.agents.quality_review_agent import QualityReviewAgent

        qa_agent = QualityReviewAgent(db=db, run_id=run_id)
        qa_result = qa_agent.run({"report_doc": report_doc, "language": language})

        _update_run(db, run_id, step="توليد ملف PDF...", progress=90)

        from app.agents.pdf_render_agent import PDFRenderAgent

        pdf_agent = PDFRenderAgent(db=db, run_id=run_id)
        pdf_result = pdf_agent.run(
            {
                "report_doc": qa_result.get("reviewed_report", report_doc),
                "charts": chart_result,
                "language": language,
                "branding": intake.get("branding", {}),
            }
        )

        _update_run(db, run_id, step="رفع التقرير إلى التخزين السحابي...", progress=95)

        # Upload PDF to S3
        import os

        pdf_path = pdf_result.get("pdf_path", "")
        s3_key = ""
        if pdf_path and os.path.exists(pdf_path):
            try:
                from app.services.storage import get_storage

                storage = get_storage()
                s3_key = (
                    f"reports/{run_id}/{pdf_result.get('pdf_filename', 'report.pdf')}"
                )
                storage.upload_pdf(pdf_path, s3_key)
                os.remove(pdf_path)  # Clean up temp file
            except Exception:
                s3_key = pdf_path  # Fallback to local path

        # Save output record
        output = ReportOutput(
            run_id=run_id,
            language=language,
            pdf_url=s3_key or pdf_path,
            page_count=pdf_result.get("page_count", 0),
            file_size_kb=pdf_result.get("file_size_kb", 0),
            generation_time_seconds=(
                datetime.utcnow() - run.started_at
            ).total_seconds(),
        )
        db.add(output)

        # Update pipeline state
        run.pipeline_state = {
            "agents_completed": list(all_results.keys()),
            "quality_score": qa_result.get("quality_score", 0),
            "page_count": pdf_result.get("page_count", 0),
        }
        run.completed_at = datetime.utcnow()
        _update_run(db, run_id, status="completed", step="اكتمل التقرير!", progress=100)

        return {
            "run_id": run_id,
            "status": "completed",
            "pdf_path": pdf_result.get("pdf_path"),
        }

    except Exception as e:
        _update_run(db, run_id, status="failed", error=str(e))
        raise
    finally:
        db.close()
