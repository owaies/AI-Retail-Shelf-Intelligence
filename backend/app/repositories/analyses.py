from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.services.vision import DetectionResult


class AnalysisRepository:
    def __init__(self, connection_factory):
        self.connection_factory = connection_factory

    def create(
        self,
        *,
        user_id: UUID,
        email: str,
        image_name: str,
        width: int,
        height: int,
        detections: list[DetectionResult],
        model_name: str,
        model_version: str,
        object_coverage: float,
    ) -> dict:
        now = datetime.now(timezone.utc)
        analysis_id = uuid4()
        with self.connection_factory() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO users (id, email) VALUES (%s, %s)
                    ON CONFLICT (id) DO UPDATE SET email = EXCLUDED.email""",
                    (user_id, email),
                )
                cur.execute(
                    """INSERT INTO analyses
                    (id, user_id, image_name, status, detection_count, image_width,
                     image_height, model_name, model_version, object_coverage, created_at, completed_at)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (analysis_id, user_id, image_name, "complete", len(detections), width,
                     height, model_name, model_version, object_coverage, now, now),
                )
                for detection in detections:
                    cur.execute(
                        """INSERT INTO detections
                        (analysis_id, class_name, confidence, x, y, width, height)
                        VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                        (analysis_id, detection.class_name, detection.confidence,
                         detection.box.x, detection.box.y, detection.box.width, detection.box.height),
                    )
            conn.commit()
        return self.get(user_id=user_id, analysis_id=analysis_id)

    def list(self, *, user_id: UUID) -> list[dict]:
        with self.connection_factory() as conn, conn.cursor() as cur:
            cur.execute(
                """SELECT id, image_name, status, detection_count, model_name,
                model_version, created_at, completed_at
                FROM analyses WHERE user_id=%s ORDER BY created_at DESC""",
                (user_id,),
            )
            columns = [d.name for d in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]

    def get(self, *, user_id: UUID, analysis_id: UUID) -> dict | None:
        with self.connection_factory() as conn, conn.cursor() as cur:
            cur.execute(
                """SELECT id, user_id, image_name, status, detection_count, image_width,
                image_height, model_name, model_version, object_coverage, created_at, completed_at
                FROM analyses WHERE id=%s AND user_id=%s""",
                (analysis_id, user_id),
            )
            row = cur.fetchone()
            if row is None:
                return None
            columns = [d.name for d in cur.description]
            result = dict(zip(columns, row))
            cur.execute(
                """SELECT class_name, confidence, x, y, width, height
                FROM detections WHERE analysis_id=%s ORDER BY id""",
                (analysis_id,),
            )
            result["detections"] = [
                {"class_name": r[0], "confidence": float(r[1]),
                 "box": {"x": float(r[2]), "y": float(r[3]), "width": float(r[4]), "height": float(r[5])}}
                for r in cur.fetchall()
            ]
            result["shelf_regions"] = []
            return result

    def delete(self, *, user_id: UUID, analysis_id: UUID) -> bool:
        with self.connection_factory() as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM analyses WHERE id=%s AND user_id=%s", (analysis_id, user_id))
            deleted = cur.rowcount == 1
            conn.commit()
            return deleted
