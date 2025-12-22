import asyncio
import sys
import os
from uuid import uuid4

# Add project root to python path
sys.path.append(os.getcwd())

from db.base import async_session
from db.models.intake import IntakeQuestion, IntakeSection
from app_logging.logger import get_logger

logger = get_logger("seed_intake_questions")

# Section ID for "Child Development & Milestones"
SECTION_ID = "a674c00e-4414-402e-a18f-7e7ba9135792"

# Intake questions data
INTAKE_QUESTIONS = [
    {
        "section_id": SECTION_ID,
        "text": "Does the child make eye contact?",
        "question_type": "RADIO",
        "options": {
            "choices": ["Yes", "No"],
            "age_group": "12 to 24 months"
        },
        "is_scorable": False,
        "scoring_logic": None,
        "order_number": 1
    },
    {
        "section_id": SECTION_ID,
        "text": "Does the child smile back when smiled at?",
        "question_type": "RADIO",
        "options": {
            "choices": ["Yes", "No"],
            "age_group": "12 to 24 months"
        },
        "is_scorable": False,
        "scoring_logic": None,
        "order_number": 2
    },
    {
        "section_id": SECTION_ID,
        "text": "Does the child respond to name and familiar voices?",
        "question_type": "RADIO",
        "options": {
            "choices": ["Yes", "No"],
            "age_group": "12 to 24 months"
        },
        "is_scorable": False,
        "scoring_logic": None,
        "order_number": 3
    },
    {
        "section_id": SECTION_ID,
        "text": "How does the child express needs (cry, gesture, babble, words)?",
        "question_type": "TEXT",
        "options": {
            "placeholder": "e.g., Cries, points, uses simple words",
            "age_group": "12 to 24 months"
        },
        "is_scorable": False,
        "scoring_logic": None,
        "order_number": 4
    },
    {
        "section_id": SECTION_ID,
        "text": "Does the child show interest in toys or people?",
        "question_type": "RADIO",
        "options": {
            "choices": ["Yes", "No"],
            "age_group": "12 to 24 months"
        },
        "is_scorable": False,
        "scoring_logic": None,
        "order_number": 5
    },
    {
        "section_id": SECTION_ID,
        "text": "How does the child react to new people or environments?",
        "question_type": "TEXT",
        "options": {
            "placeholder": "e.g., Shy, curious, fearful, excited",
            "age_group": "12 to 24 months"
        },
        "is_scorable": False,
        "scoring_logic": None,
        "order_number": 6
    },
    {
        "section_id": SECTION_ID,
        "text": "Does the child crawl/walk?",
        "question_type": "RADIO",
        "options": {
            "choices": ["Yes", "No"],
            "age_group": "12 to 24 months"
        },
        "is_scorable": False,
        "scoring_logic": None,
        "order_number": 7
    },
    {
        "section_id": SECTION_ID,
        "text": "Feeding habits (self-feeding, spoon, bottle, mouthing objects)?",
        "question_type": "TEXT",
        "options": {
            "placeholder": "e.g., Self-feeds with hands, uses bottle, mouths toys",
            "age_group": "12 to 24 months"
        },
        "is_scorable": False,
        "scoring_logic": None,
        "order_number": 8
    },
    {
        "section_id": SECTION_ID,
        "text": "Sleep pattern?",
        "question_type": "TEXT",
        "options": {
            "placeholder": "e.g., Sleeps through night, naps twice daily",
            "age_group": "12 to 24 months"
        },
        "is_scorable": False,
        "scoring_logic": None,
        "order_number": 9
    },
    {
        "section_id": SECTION_ID,
        "text": "Does the child imitate simple actions (clapping, waving)?",
        "question_type": "RADIO",
        "options": {
            "choices": ["Yes", "No"],
            "age_group": "12 to 24 months"
        },
        "is_scorable": False,
        "scoring_logic": None,
        "order_number": 10
    },
    {
        "section_id": SECTION_ID,
        "text": "How many words does the child use?",
        "question_type": "TEXT",
        "options": {
            "placeholder": "e.g., 5-10 words, 20-30 words, None yet",
            "age_group": "24 to 36 months"
        },
        "is_scorable": False,
        "scoring_logic": None,
        "order_number": 11
    },
    {
        "section_id": SECTION_ID,
        "text": "Does the child understand simple instructions (\"give me the ball\")?",
        "question_type": "RADIO",
        "options": {
            "choices": ["Yes", "No"],
            "age_group": "24 to 36 months"
        },
        "is_scorable": False,
        "scoring_logic": None,
        "order_number": 12
    },
    {
        "section_id": SECTION_ID,
        "text": "Does the child point to show interest?",
        "question_type": "RADIO",
        "options": {
            "choices": ["Yes", "No"],
            "age_group": "24 to 36 months"
        },
        "is_scorable": False,
        "scoring_logic": None,
        "order_number": 13
    },
    {
        "section_id": SECTION_ID,
        "text": "Does the child play pretend (feed doll, drive toy car)?",
        "question_type": "RADIO",
        "options": {
            "choices": ["Yes", "No"],
            "age_group": "24 to 36 months"
        },
        "is_scorable": False,
        "scoring_logic": None,
        "order_number": 14
    },
    {
        "section_id": SECTION_ID,
        "text": "Does the child enjoy being around other children?",
        "question_type": "RADIO",
        "options": {
            "choices": ["Yes", "No"],
            "age_group": "24 to 36 months"
        },
        "is_scorable": False,
        "scoring_logic": None,
        "order_number": 15
    },
    {
        "section_id": SECTION_ID,
        "text": "Any repetitive actions (spinning, lining up toys, hand-flapping)?",
        "question_type": "RADIO",
        "options": {
            "choices": ["Yes", "No"],
            "isDropdown": True,
            "followUpQuestion": "If Yes, please describe the repetitive behaviors",
            "age_group": "24 to 36 months"
        },
        "is_scorable": False,
        "scoring_logic": None,
        "order_number": 16
    },
    {
        "section_id": SECTION_ID,
        "text": "Toilet training progress?",
        "question_type": "TEXT",
        "options": {
            "placeholder": "e.g., Not started, In progress, Fully trained",
            "age_group": "24 to 36 months"
        },
        "is_scorable": False,
        "scoring_logic": None,
        "order_number": 17
    },
    {
        "section_id": SECTION_ID,
        "text": "Eating preferences and aversions?",
        "question_type": "TEXT",
        "options": {
            "placeholder": "e.g., Prefers sweet foods, avoids vegetables",
            "age_group": "24 to 36 months"
        },
        "is_scorable": False,
        "scoring_logic": None,
        "order_number": 18
    },
    {
        "section_id": SECTION_ID,
        "text": "Any tantrums or rigid behaviors?",
        "question_type": "RADIO",
        "options": {
            "choices": ["Yes", "No"],
            "isDropdown": True,
            "followUpQuestion": "If Yes, please describe frequency and triggers",
            "age_group": "24 to 36 months"
        },
        "is_scorable": False,
        "scoring_logic": None,
        "order_number": 19
    },
    {
        "section_id": SECTION_ID,
        "text": "Can the child speak in short sentences?",
        "question_type": "RADIO",
        "options": {
            "choices": ["Yes", "No"],
            "age_group": "36 to 48 months"
        },
        "is_scorable": False,
        "scoring_logic": None,
        "order_number": 20
    },
    {
        "section_id": SECTION_ID,
        "text": "Can the child follow 2-step instructions?",
        "question_type": "RADIO",
        "options": {
            "choices": ["Yes", "No"],
            "isDropdown": True,
            "followUpQuestion": "If Yes, please give examples (e.g., 'Pick up the toy and put it in the box')",
            "age_group": "36 to 48 months"
        },
        "is_scorable": False,
        "scoring_logic": None,
        "order_number": 21
    },
    {
        "section_id": SECTION_ID,
        "text": "Does the child engage in group play or parallel play?",
        "question_type": "TEXT",
        "options": {
            "placeholder": "e.g., Plays alongside others, plays with others",
            "age_group": "36 to 48 months"
        },
        "is_scorable": False,
        "scoring_logic": None,
        "order_number": 22
    },
    {
        "section_id": SECTION_ID,
        "text": "Does the child make friends easily?",
        "question_type": "RADIO",
        "options": {
            "choices": ["Yes", "No"],
            "age_group": "36 to 48 months"
        },
        "is_scorable": False,
        "scoring_logic": None,
        "order_number": 23
    },
    {
        "section_id": SECTION_ID,
        "text": "Can the child feed and dress with some independence?",
        "question_type": "RADIO",
        "options": {
            "choices": ["Yes", "No"],
            "age_group": "36 to 48 months"
        },
        "is_scorable": False,
        "scoring_logic": None,
        "order_number": 24
    },
    {
        "section_id": SECTION_ID,
        "text": "Can the child identify colors, shapes, or familiar objects?",
        "question_type": "RADIO",
        "options": {
            "choices": ["Yes", "No"],
            "age_group": "36 to 48 months"
        },
        "is_scorable": False,
        "scoring_logic": None,
        "order_number": 25
    },
    {
        "section_id": SECTION_ID,
        "text": "Does the child show empathy or notice others' feelings?",
        "question_type": "RADIO",
        "options": {
            "choices": ["Yes", "No"],
            "age_group": "36 to 48 months"
        },
        "is_scorable": False,
        "scoring_logic": None,
        "order_number": 26
    },
    {
        "section_id": SECTION_ID,
        "text": "Any fears or sensitivities (sounds, textures, crowds)?",
        "question_type": "RADIO",
        "options": {
            "choices": ["Yes", "No"],
            "isDropdown": True,
            "followUpQuestion": "If Yes, please describe the specific fears or sensitivities",
            "age_group": "36 to 48 months"
        },
        "is_scorable": False,
        "scoring_logic": None,
        "order_number": 27
    },
    {
        "section_id": SECTION_ID,
        "text": "Can the child narrate small stories or describe pictures?",
        "question_type": "RADIO",
        "options": {
            "choices": ["Yes", "No"],
            "age_group": "48 to 60 months"
        },
        "is_scorable": False,
        "scoring_logic": None,
        "order_number": 28
    },
    {
        "section_id": SECTION_ID,
        "text": "Can the child manage toilet needs independently?",
        "question_type": "RADIO",
        "options": {
            "choices": ["Yes", "No"],
            "age_group": "48 to 60 months"
        },
        "is_scorable": False,
        "scoring_logic": None,
        "order_number": 29
    },
    {
        "section_id": SECTION_ID,
        "text": "Does the child participate in structured play or preschool activities?",
        "question_type": "RADIO",
        "options": {
            "choices": ["Yes", "No"],
            "age_group": "48 to 60 months"
        },
        "is_scorable": False,
        "scoring_logic": None,
        "order_number": 30
    },
    {
        "section_id": SECTION_ID,
        "text": "How does the child react to changes in routine?",
        "question_type": "TEXT",
        "options": {
            "placeholder": "e.g., Adapts easily, gets upset, needs preparation",
            "age_group": "48 to 60 months"
        },
        "is_scorable": False,
        "scoring_logic": None,
        "order_number": 31
    },
    {
        "section_id": SECTION_ID,
        "text": "Does the child understand time-related concepts (today, tomorrow)?",
        "question_type": "RADIO",
        "options": {
            "choices": ["Yes", "No"],
            "age_group": "48 to 60 months"
        },
        "is_scorable": False,
        "scoring_logic": None,
        "order_number": 32
    },
    {
        "section_id": SECTION_ID,
        "text": "Attention span during storytelling or play?",
        "question_type": "TEXT",
        "options": {
            "placeholder": "e.g., 5-10 minutes, 15-20 minutes, Very short",
            "age_group": "48 to 60 months"
        },
        "is_scorable": False,
        "scoring_logic": None,
        "order_number": 33
    },
    {
        "section_id": SECTION_ID,
        "text": "How is the interaction with peers and adults?",
        "question_type": "TEXT",
        "options": {
            "placeholder": "Please describe the child's social interactions",
            "age_group": "48 to 60 months"
        },
        "is_scorable": False,
        "scoring_logic": None,
        "order_number": 34
    },
    {
        "section_id": SECTION_ID,
        "text": "How is the interaction with peers and adults?",
        "question_type": "TEXT",
        "options": {
            "placeholder": "Please describe the child's social interactions",
            "age_group": "48 to 60 months"
        },
        "is_scorable": False,
        "scoring_logic": None,
        "order_number": 35
    },
    {
        "section_id": SECTION_ID,
        "text": "Does the parent feel the child's development is similar to peers?",
        "question_type": "RADIO",
        "options": {
            "choices": ["Yes", "No"],
            "isDropdown": True,
            "followUpQuestion": "If No, please describe the differences you've noticed",
            "age_group": "48 to 60 months"
        },
        "is_scorable": False,
        "scoring_logic": None,
        "order_number": 36
    },
    {
        "section_id": SECTION_ID,
        "text": "Who does the child go to for comfort - mother, father, both?",
        "question_type": "RADIO",
        "options": {
            "choices": ["Mother", "Father", "Both", "Others"],
            "age_group": "24 to 60 months"
        },
        "is_scorable": False,
        "scoring_logic": None,
        "order_number": 37
    }
]


async def seed_intake_questions():
    """
    Seed intake questions for family demographics and basic information.
    """
    try:
        async with async_session() as db:
            # Check if section exists
            section = await db.get(IntakeSection, SECTION_ID)
            if not section:
                logger.error(f"Section with ID {SECTION_ID} does not exist. Please create the section first.")
                return
            
            logger.info(f"Found section: {section.title}")
            
            # Check existing questions
            from sqlalchemy import select
            stmt = select(IntakeQuestion).where(IntakeQuestion.section_id == SECTION_ID)
            result = await db.execute(stmt)
            existing_questions = list(result.scalars().all())
            
            if existing_questions:
                logger.warning(f"Found {len(existing_questions)} existing questions in this section.")
                response = input("Do you want to delete existing questions and reseed? (yes/no): ")
                if response.lower() == 'yes':
                    for question in existing_questions:
                        await db.delete(question)
                    await db.commit()
                    logger.info("Deleted existing questions.")
                else:
                    logger.info("Keeping existing questions. Aborting seed operation.")
                    return
            
            # Insert questions
            logger.info(f"Inserting {len(INTAKE_QUESTIONS)} intake questions...")
            
            for idx, question_data in enumerate(INTAKE_QUESTIONS, 1):
                question = IntakeQuestion(
                    id=str(uuid4()),
                    **question_data
                )
                db.add(question)
                logger.info(f"  [{idx}/{len(INTAKE_QUESTIONS)}] Added: {question.text[:60]}...")
            
            await db.commit()
            logger.info(f"✅ Successfully seeded {len(INTAKE_QUESTIONS)} intake questions!")
            
            # Verify
            stmt = select(IntakeQuestion).where(IntakeQuestion.section_id == SECTION_ID)
            result = await db.execute(stmt)
            final_count = len(list(result.scalars().all()))
            logger.info(f"✅ Verification: {final_count} questions now exist in section {SECTION_ID}")
            
    except Exception as e:
        logger.error(f"❌ Error seeding intake questions: {e}", exc_info=True)
        raise


async def create_section_if_not_exists():
    """
    Create the intake section if it doesn't exist.
    """
    try:
        async with async_session() as db:
            section = await db.get(IntakeSection, SECTION_ID)
            
            if not section:
                logger.info(f"Section {SECTION_ID} does not exist. Creating it...")
                section = IntakeSection(
                    id=SECTION_ID,
                    title="Child Development & Milestones",
                    description="Comprehensive developmental assessment across age ranges (1-5 years)",
                    order_number=8,
                    is_active=True
                )
                db.add(section)
                await db.commit()
                logger.info(f"✅ Created section: {section.title}")
            else:
                logger.info(f"✅ Section already exists: {section.title}")
                
    except Exception as e:
        logger.error(f"❌ Error creating section: {e}", exc_info=True)
        raise


async def main():
    """Main function to run the seeding process."""
    logger.info("=" * 80)
    logger.info("Starting Intake Questions Seeding Process")
    logger.info("=" * 80)
    
    # First, ensure section exists
    await create_section_if_not_exists()
    
    # Then seed questions
    await seed_intake_questions()
    
    logger.info("=" * 80)
    logger.info("Intake Questions Seeding Process Completed")
    logger.info("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
