"""
Migration Script: Recalculate Scores for Existing Completed Responses

This script recalculates total_score and max_possible_score for all existing
COMPLETED AssessmentResponse records that have NULL scores.

Run this ONCE after deploying the score calculation fix.

Usage:
    python scripts/migrate_recalculate_scores.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from db.base import async_session
from db.models.assessment import (
    AssessmentResponse,
    AssessmentQuestionAnswer,
    AssessmentQuestion,
    AssessmentStatus
)
from app_logging.logger import get_logger

logger = get_logger(__name__)


async def recalculate_response_scores(db: AsyncSession, response_id: str) -> tuple[int, int]:
    """
    Recalculate scores for a single response.
    
    Returns:
        (total_score, max_possible_score)
    """
    # Sum all answer scores
    total_score_result = await db.execute(
        select(func.sum(AssessmentQuestionAnswer.score))
        .where(AssessmentQuestionAnswer.response_id == response_id)
    )
    total_score = total_score_result.scalar() or 0
    
    # Get all answered question IDs
    answered_question_ids_result = await db.execute(
        select(AssessmentQuestionAnswer.question_id)
        .where(AssessmentQuestionAnswer.response_id == response_id)
    )
    answered_question_ids = [row[0] for row in answered_question_ids_result.all()]
    
    # Calculate max possible score
    max_possible_score = 0
    if answered_question_ids:
        questions_result = await db.execute(
            select(AssessmentQuestion)
            .where(AssessmentQuestion.id.in_(answered_question_ids))
        )
        questions = questions_result.scalars().all()
        
        for question in questions:
            age_protocol = question.age_protocol or {}
            scoring = age_protocol.get("scoring", {})
            max_score = scoring.get("max_score", 4)  # Default to 4
            max_possible_score += max_score
    
    return total_score, max_possible_score


async def migrate_scores():
    """Main migration function."""
    logger.info("Starting score migration...")
    
    async with async_session() as db:
        # Get all COMPLETED responses with NULL scores
        result = await db.execute(
            select(AssessmentResponse)
            .where(
                AssessmentResponse.status == AssessmentStatus.COMPLETED,
                AssessmentResponse.total_score.is_(None)
            )
        )
        responses = result.scalars().all()
        
        total_responses = len(responses)
        logger.info(f"Found {total_responses} completed responses with NULL scores")
        
        if total_responses == 0:
            logger.info("No responses to migrate. Exiting.")
            return
        
        updated_count = 0
        failed_count = 0
        
        for idx, response in enumerate(responses, 1):
            try:
                # Recalculate scores
                total_score, max_possible_score = await recalculate_response_scores(
                    db, response.id
                )
                
                # Update response
                response.total_score = total_score
                response.max_possible_score = max_possible_score
                
                updated_count += 1
                
                logger.info(
                    f"[{idx}/{total_responses}] Updated response {response.id}: "
                    f"score={total_score}/{max_possible_score}"
                )
                
                # Commit in batches of 10
                if updated_count % 10 == 0:
                    await db.commit()
                    logger.info(f"Committed batch (total: {updated_count})")
                
            except Exception as e:
                failed_count += 1
                logger.error(
                    f"Failed to update response {response.id}: {e}",
                    exc_info=True
                )
        
        # Final commit
        await db.commit()
        
        logger.info(
            f"\n{'='*60}\n"
            f"Migration Complete!\n"
            f"  Total responses: {total_responses}\n"
            f"  Updated: {updated_count}\n"
            f"  Failed: {failed_count}\n"
            f"{'='*60}\n"
        )
        
        logger.info(
            "\nNext steps:\n"
            "1. Delete existing pool summaries: DELETE FROM report.pool_summaries;\n"
            "2. Delete existing final reports: DELETE FROM report.final_reports;\n"
            "3. Call /generate-missing endpoint for each child to regenerate reports\n"
        )


if __name__ == "__main__":
    asyncio.run(migrate_scores())
