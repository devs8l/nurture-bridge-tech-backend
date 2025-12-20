import asyncio
import sys
import os
import json
from datetime import datetime

# Add project root to python path
sys.path.append(os.getcwd())

from db.base import async_session
from db.models.assessment import AssessmentSection
from app_logging.logger import get_logger

logger = get_logger("seed_sections")

# Section data from sections.json
SECTIONS_DATA = [
    {
        "id": "470926f1-81b7-46ea-a98d-29a695616a21",
        "title": "Cognition and play skills",
        "description": "string",
        "order_number": 5,
        "is_active": True,
        "created_at": "2025-12-17 10:31:31.147164",
        "updated_at": "2025-12-17 10:31:31.147164"
    },
    {
        "id": "51ac875c-3011-48ac-84e0-2e5817bbf8ba",
        "title": "Random Repetitive Behavior and Sensory Processing",
        "description": "string",
        "order_number": 3,
        "is_active": True,
        "created_at": "2025-12-17 06:59:49.145015",
        "updated_at": "2025-12-17 06:59:49.145015"
    },
    {
        "id": "a7eb6907-b791-4874-b0d1-f646f1515ea4",
        "title": "Social Reciprocity",
        "description": "string",
        "order_number": 1,
        "is_active": True,
        "created_at": "2025-12-16 19:11:44.473355",
        "updated_at": "2025-12-16 19:11:44.473355"
    },
    {
        "id": "ccdaae62-69b7-4770-ba54-77e138c5ad24",
        "title": "Adaptive Behavior and Self help skills",
        "description": "string",
        "order_number": 4,
        "is_active": True,
        "created_at": "2025-12-17 10:28:45.345166",
        "updated_at": "2025-12-17 10:28:45.345166"
    },
    {
        "id": "f3622868-5fc1-42b0-8a8c-eead3cdb3efc",
        "title": "Language and Communication",
        "description": "string",
        "order_number": 2,
        "is_active": True,
        "created_at": "2025-12-17 06:57:46.683324",
        "updated_at": "2025-12-17 06:57:46.683324"
    }
]


async def seed_sections():
    """
    Seed assessment sections into the database.
    This will insert or update sections based on their ID.
    """
    logger.info("🌱 Starting sections seed...")
    
    async with async_session() as db:
        try:
            from sqlalchemy import select
            
            created_count = 0
            updated_count = 0
            skipped_count = 0
            
            for section_data in SECTIONS_DATA:
                # Check if section already exists
                result = await db.execute(
                    select(AssessmentSection).where(AssessmentSection.id == section_data["id"])
                )
                existing_section = result.scalars().first()
                
                if existing_section:
                    # Update existing section
                    logger.info(f"📝 Section '{section_data['title']}' already exists, updating...")
                    existing_section.title = section_data["title"]
                    existing_section.description = section_data["description"]
                    existing_section.order_number = section_data["order_number"]
                    existing_section.is_active = section_data["is_active"]
                    updated_count += 1
                else:
                    # Create new section
                    logger.info(f"✨ Creating section: {section_data['title']}")
                    new_section = AssessmentSection(
                        id=section_data["id"],
                        title=section_data["title"],
                        description=section_data["description"],
                        order_number=section_data["order_number"],
                        is_active=section_data["is_active"]
                    )
                    db.add(new_section)
                    created_count += 1
            
            # Commit all changes
            await db.commit()
            
            logger.info("=" * 50)
            logger.info(f"✅ Sections seeding completed!")
            logger.info(f"   📦 Created: {created_count}")
            logger.info(f"   🔄 Updated: {updated_count}")
            logger.info(f"   ⏭️  Skipped: {skipped_count}")
            logger.info("=" * 50)
            
            # Display all sections ordered by order_number
            logger.info("\n📋 Current sections in database:")
            result = await db.execute(
                select(AssessmentSection).order_by(AssessmentSection.order_number)
            )
            sections = result.scalars().all()
            
            for section in sections:
                status = "✓" if section.is_active else "✗"
                logger.info(f"   {status} [{section.order_number}] {section.title}")
            
        except Exception as e:
            logger.error(f"❌ Error seeding sections: {e}")
            await db.rollback()
            raise
        finally:
            await db.close()


async def main():
    """Main entry point"""
    try:
        await seed_sections()
    except Exception as e:
        logger.error(f"Failed to seed sections: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
