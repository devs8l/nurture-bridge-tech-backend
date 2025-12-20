import asyncio
import sys
import os
import json
from datetime import datetime

# Add project root to python path
sys.path.append(os.getcwd())

from db.base import async_session
from db.models.assessment import AssessmentQuestion, AssessmentSection
from app_logging.logger import get_logger

logger = get_logger("seed_questions")

# Question data from questions.json
QUESTIONS_DATA = [
    {
        "id": "02c75828-d386-4f86-a4fa-630c0079a3d1",
        "section_id": "f3622868-5fc1-42b0-8a8c-eead3cdb3efc",
        "text": "Does the child show interest when you explain about their actions?",
        "min_age_months": 30,
        "max_age_months": 60,
        "age_protocol": {
            "example": "Interest when you explain dangers: matchsticks, fire, hot cooker, not opening door alone, holding hands on the road.",
            "scoring_pattern": "Applicable 30–60 months."
        },
        "order_number": 5
    },
    {
        "id": "044275ff-077a-4b0f-98c2-6e117de2a994",
        "section_id": "51ac875c-3011-48ac-84e0-2e5817bbf8ba",
        "text": "Does the child show repetitive movements?",
        "min_age_months": 12,
        "max_age_months": 60,
        "age_protocol": {
            "example": "Flapping hands, rocking on a chair, spinning in circles, repeated jumping, moving hands near eyes, flickering fingers.",
            "scoring_pattern": "Common protocol for repetitive movements."
        },
        "order_number": 1
    },
    {
        "id": "08d6e730-654e-4cd8-b4fa-ca21fa3e3d0f",
        "section_id": "470926f1-81b7-46ea-a98d-29a695616a21",
        "text": "Does the child show emerging symbolic or pretend play skills?",
        "min_age_months": 36,
        "max_age_months": 60,
        "age_protocol": {
            "example": "Pretending to be a doctor, chef, teacher, or using objects symbolically like a stick as a spoon; role-playing characters like Hanuman or Superman.",
            "scoring_pattern": "Common protocol for symbolic play development."
        },
        "order_number": 5
    },
    {
        "id": "0e09234c-ecaf-4b5a-a544-8a24db984043",
        "section_id": "ccdaae62-69b7-4770-ba54-77e138c5ad24",
        "text": "Does the child use household objects appropriately?",
        "min_age_months": 20,
        "max_age_months": 60,
        "age_protocol": {
            "example": "Using spoon to eat, cup to drink, straw to sip juice.",
            "scoring_pattern": "Common protocol for object-use skills."
        },
        "order_number": 4
    },
    {
        "id": "0f08848b-4bef-43b6-bcbc-afe4153e9b47",
        "section_id": "470926f1-81b7-46ea-a98d-29a695616a21",
        "text": "Does the child show curiosity and exploration during play enjoying with the adult and not play alone?",
        "min_age_months": 24,
        "max_age_months": 60,
        "age_protocol": {
            "example": "Playing along with adults who join, not throwing toys or leaving when someone joins.",
            "scoring_pattern": "Common protocol for joint play curiosity."
        },
        "order_number": 2
    },
    {
        "id": "124abc6d-dedd-4fa3-8ee3-149a89d55208",
        "section_id": "51ac875c-3011-48ac-84e0-2e5817bbf8ba",
        "text": "Does the child show repetitive use of objects?",
        "min_age_months": 12,
        "max_age_months": 60,
        "age_protocol": {
            "example": "Tapping objects repeatedly, lining toys, spinning wheels, pouring water or sand repeatedly, playing with thread or sticks, repeatedly dropping objects and watching them.",
            "scoring_pattern": "Common protocol for object-based repetition."
        },
        "order_number": 2
    },
    {
        "id": "13f06bc9-927e-415d-b96c-68c984a49983",
        "section_id": "f3622868-5fc1-42b0-8a8c-eead3cdb3efc",
        "text": "Does the child use pronouns correctly?",
        "min_age_months": 36,
        "max_age_months": 60,
        "age_protocol": {
            "example": "Uses proper pronouns and gender terms, self‐corrects mistakes.",
            "scoring_pattern": "Applicable only 36–60 months."
        },
        "order_number": 8
    },
    {
        "id": "15863a8e-f933-4702-9628-11bf550c8874",
        "section_id": "a7eb6907-b791-4874-b0d1-f646f1515ea4",
        "text": "Does the child engage in simple back-and-forth interactions with parents?",
        "min_age_months": 0,
        "max_age_months": 60,
        "age_protocol": {
            "example": "0–24m: repeats words/sounds like mmm, ooo, auu, uses gibberish or tries to repeat parent's words. 25–48m: uses proto-words to call parent and express hunger, sleep, play needs. 49–60m: interacts freely with parents.",
            "scoring_pattern": "Age-band based scoring 0–24m, 25–48m, 49–60m."
        },
        "order_number": 4
    },
    {
        "id": "1db8c3bc-05fb-413e-be16-982a7fef5143",
        "section_id": "ccdaae62-69b7-4770-ba54-77e138c5ad24",
        "text": "Does the child recognize familiar people and respond appropriately?",
        "min_age_months": 24,
        "max_age_months": 60,
        "age_protocol": {
            "example": "Hugging familiar people, going to grandparents, playing with known cousins.",
            "scoring_pattern": "Common protocol for social familiarity."
        },
        "order_number": 8
    },
    {
        "id": "1f434794-9938-489a-947a-43471ed116ce",
        "section_id": "ccdaae62-69b7-4770-ba54-77e138c5ad24",
        "text": "Does the child understand basic safety rules?",
        "min_age_months": 36,
        "max_age_months": 60,
        "age_protocol": {
            "example": "Not fidgeting on two-wheelers, sitting properly in a car, following road safety.",
            "scoring_pattern": "Common protocol for safety understanding."
        },
        "order_number": 9
    },
    {
        "id": "25d4f0f5-10f3-426d-9c6e-cb3a51565db7",
        "section_id": "470926f1-81b7-46ea-a98d-29a695616a21",
        "text": "Does the child maintain attention for age-appropriate durations?",
        "min_age_months": 12,
        "max_age_months": 60,
        "age_protocol": {
            "example": "12–24m: 5–8 minutes attention in play like peek-a-boo or tickle games. 24–60m: mix of movement games and sit-and-play activities like racing tracks, pretend kitchen, art & craft.",
            "scoring_pattern": "Common protocol for attention span during play."
        },
        "order_number": 4
    },
    {
        "id": "2654578d-1c2e-4c03-a525-e4879cebf03b",
        "section_id": "f3622868-5fc1-42b0-8a8c-eead3cdb3efc",
        "text": "How many words does the child use independently (not repeating after parent)?",
        "min_age_months": 12,
        "max_age_months": 60,
        "age_protocol": {
            "example": "12–20m: ~50 words (toys, parents, animals, foods like roti, dosa; give me, take it, no). 21–30m: ~500 words for expressing many needs. 31–60m: ~1000+ words, learning from school, talking to neighbors, complaining, narrating events.",
            "scoring_pattern": "Age‐specific scaling: 50 words → 500 words → 1000+ words."
        },
        "order_number": 2
    },
    {
        "id": "2f431378-8841-4377-b06f-6b859c761b8b",
        "section_id": "ccdaae62-69b7-4770-ba54-77e138c5ad24",
        "text": "Is the child toilet trained or showing readiness?",
        "min_age_months": 20,
        "max_age_months": 60,
        "age_protocol": {
            "example": "Indicating discomfort or wetness, sitting on toilet, using toilet with support.",
            "scoring_pattern": "Common protocol for toileting readiness."
        },
        "order_number": 3
    },
    {
        "id": "3275e602-bad7-4e68-9362-c767053f493b",
        "section_id": "a7eb6907-b791-4874-b0d1-f646f1515ea4",
        "text": "Does the child maintain appropriate eye contact during interaction?",
        "min_age_months": 0,
        "max_age_months": 60,
        "age_protocol": {
            "example": "Child looks at you while talking or when you explain play instructions, or when being disciplined.",
            "scoring_pattern": "Common protocol"
        },
        "order_number": 6
    },
    {
        "id": "3eafa079-6b45-4569-92aa-02b8f3511b71",
        "section_id": "ccdaae62-69b7-4770-ba54-77e138c5ad24",
        "text": "Can the child feed themselves appropriately?",
        "min_age_months": 20,
        "max_age_months": 60,
        "age_protocol": {
            "example": "Eating finger foods, eating with hands, eating with a spoon.",
            "scoring_pattern": "Common protocol for feeding independence."
        },
        "order_number": 1
    },
    {
        "id": "40c3c017-14f7-4bf9-a07a-c6b463b65f56",
        "section_id": "51ac875c-3011-48ac-84e0-2e5817bbf8ba",
        "text": "Does the child have unusual feeding preferences due to sensory issues?",
        "min_age_months": 12,
        "max_age_months": 60,
        "age_protocol": {
            "example": "Eating plain rice, avoiding mixed textures like upma, avoiding coriander leaves in food, preferring bland or very spicy food.",
            "scoring_pattern": "Common protocol for sensory-based feeding."
        },
        "order_number": 13
    },
    {
        "id": "40caa6c1-089f-44c0-92c4-58a934f9f72f",
        "section_id": "a7eb6907-b791-4874-b0d1-f646f1515ea4",
        "text": "Does the child imitate other people's actions?",
        "min_age_months": 0,
        "max_age_months": 60,
        "age_protocol": {
            "example": "Imitates clapping, waving, copying dance steps, playing pretend phone calls, cooking, shaving, combing hair.",
            "scoring_pattern": "Common protocol"
        },
        "order_number": 5
    },
    {
        "id": "49ef1977-6d55-419d-8721-e258f0cf5997",
        "section_id": "51ac875c-3011-48ac-84e0-2e5817bbf8ba",
        "text": "Does the child react strongly to grooming activities?",
        "min_age_months": 12,
        "max_age_months": 60,
        "age_protocol": {
            "example": "Strong reactions during haircuts, nail cutting, head wash, face wash, brushing teeth, tongue cleaning, applying lotion.",
            "scoring_pattern": "Common protocol for grooming sensitivity."
        },
        "order_number": 12
    },
    {
        "id": "4b173446-50c7-47b5-b67c-d39204219c7c",
        "section_id": "51ac875c-3011-48ac-84e0-2e5817bbf8ba",
        "text": "Does the child show unusual visual behaviours?",
        "min_age_months": 12,
        "max_age_months": 60,
        "age_protocol": {
            "example": "Looking at objects from corner of eyes, flipping pages rapidly without reading, pouring water/sand repeatedly, watching a spinning fan.",
            "scoring_pattern": "Common protocol for visual patterns."
        },
        "order_number": 6
    },
    {
        "id": "4c05cab2-9211-4a71-9708-4ce3ef224c75",
        "section_id": "a7eb6907-b791-4874-b0d1-f646f1515ea4",
        "text": "Does the child initiate interaction with others in the family/friends other than parents?",
        "min_age_months": 0,
        "max_age_months": 60,
        "age_protocol": {
            "example": "Approaches grandparents for needs, plays with siblings, gives hi-fi or shake hands with peers in parks. Till 2 years actions/gestures are sufficient; above 2 years verbal interaction required.",
            "scoring_pattern": "Till 2 years – gestures allowed. Above 2 years – verbal interaction required for highest score."
        },
        "order_number": 3
    },
    {
        "id": "55e24929-5350-4458-88da-0c3d039678c2",
        "section_id": "a7eb6907-b791-4874-b0d1-f646f1515ea4",
        "text": "Does the child respond when their name is called?",
        "min_age_months": 0,
        "max_age_months": 60,
        "age_protocol": {
            "example": "You are working in the living room and your child is near the main door—does the child respond when you call their name? Or when playing, does the child respond when asked: 'Sara, shall I tickle you more?'",
            "scoring_pattern": "Common protocol"
        },
        "order_number": 1
    },
    {
        "id": "62901ad0-9232-4e96-9e75-285cb1157bbb",
        "section_id": "ccdaae62-69b7-4770-ba54-77e138c5ad24",
        "text": "Can the child dress/undress with age-appropriate help?",
        "min_age_months": 36,
        "max_age_months": 60,
        "age_protocol": {
            "example": "Removing pants, wearing shorts, pulling a T-shirt with little help.",
            "scoring_pattern": "Common protocol for dressing independence."
        },
        "order_number": 2
    },
    {
        "id": "6d051d8c-6037-49ef-b1f1-543aa3f85453",
        "section_id": "51ac875c-3011-48ac-84e0-2e5817bbf8ba",
        "text": "Does the child insist on specific rituals?",
        "min_age_months": 12,
        "max_age_months": 60,
        "age_protocol": {
            "example": "Closing doors only in a certain manner, arranging objects repeatedly, rigid eating habits, maintaining strict routines.",
            "scoring_pattern": "Common protocol for ritualistic behaviour."
        },
        "order_number": 8
    },
    {
        "id": "7221db4b-835d-484a-a3e6-1d21bc081415",
        "section_id": "a7eb6907-b791-4874-b0d1-f646f1515ea4",
        "text": "Does the child share their happiness with others?",
        "min_age_months": 30,
        "max_age_months": 60,
        "age_protocol": {
            "example": "Smiling while playing at park, sharing chocolate, showing new toy to friend or sibling.",
            "scoring_pattern": "Common protocol"
        },
        "order_number": 7
    },
    {
        "id": "7307791e-ecf4-4475-af0f-1b985903cc9c",
        "section_id": "a7eb6907-b791-4874-b0d1-f646f1515ea4",
        "text": "Does the child seek attention from adults in the family through positive behavior?",
        "min_age_months": 0,
        "max_age_months": 60,
        "age_protocol": {
            "example": "0–36m: Child shows biscuit to mother, brings toy to parent, brings scooter keys to say 'let's go out', or tries to snatch parent's phone or glasses. 37–60m: Child waits for approval before opening door when bell rings; waits before taking papad from your plate.",
            "scoring_pattern": "0–36m and 37–60m have different scoring. Age-specific scoring applies."
        },
        "order_number": 2
    },
    {
        "id": "7d1531d2-f032-432f-af68-7ff6098a58e6",
        "section_id": "a7eb6907-b791-4874-b0d1-f646f1515ea4",
        "text": "Does the child participate in group or peer activities?",
        "min_age_months": 12,
        "max_age_months": 60,
        "age_protocol": {
            "example": "Plays with peers, hugs, shares toys when prompted, asks a friend for a toy, sits and plays in sand with another kid.",
            "scoring_pattern": "Common protocol"
        },
        "order_number": 9
    },
    {
        "id": "7e7439bb-f203-4019-831a-95e84ec909b2",
        "section_id": "ccdaae62-69b7-4770-ba54-77e138c5ad24",
        "text": "Does the child follow daily routines without distress?",
        "min_age_months": 30,
        "max_age_months": 60,
        "age_protocol": {
            "example": "Getting ready for school, eating breakfast on time, eating with family.",
            "scoring_pattern": "Common protocol for routine participation."
        },
        "order_number": 5
    },
    {
        "id": "85230381-7ac3-42b4-8865-b82ae7d43f63",
        "section_id": "51ac875c-3011-48ac-84e0-2e5817bbf8ba",
        "text": "Does the child have unusual sensory interests?",
        "min_age_months": 12,
        "max_age_months": 60,
        "age_protocol": {
            "example": "Sniffing people, touching different surfaces, tasting or mouthing non-food items.",
            "scoring_pattern": "Common protocol for sensory interest."
        },
        "order_number": 4
    },
    {
        "id": "8ea381bc-1dee-45af-a80a-9c996be6b80f",
        "section_id": "f3622868-5fc1-42b0-8a8c-eead3cdb3efc",
        "text": "Does the child follow complex commands at home or school?",
        "min_age_months": 36,
        "max_age_months": 60,
        "age_protocol": {
            "example": "Home examples: 'Give this from the kitchen', 'Choose your dress', 'Bring towel for shower', 'Pass diaper to baby brother'. School: 'Form a line', 'Join hands for prayer', 'Take out notebook', 'Submit books', 'Sit in groups of 3'.",
            "scoring_pattern": "Applicable only from 36–60 months."
        },
        "order_number": 4
    },
    {
        "id": "97334bff-13c6-404c-8d31-cab3e3e1e9dc",
        "section_id": "470926f1-81b7-46ea-a98d-29a695616a21",
        "text": "Does the child solve simple age-appropriate problems (puzzles)?",
        "min_age_months": 24,
        "max_age_months": 60,
        "age_protocol": {
            "example": "Solving 4-piece puzzles initially and progressing to 40+ piece puzzles.",
            "scoring_pattern": "Common protocol for puzzle/problem solving."
        },
        "order_number": 3
    },
    {
        "id": "987c7466-c486-4ad4-8db0-d3e5dfc68483",
        "section_id": "51ac875c-3011-48ac-84e0-2e5817bbf8ba",
        "text": "Does the child have intense or very specific interests?",
        "min_age_months": 12,
        "max_age_months": 60,
        "age_protocol": {
            "example": "Reading a lot of books, sketching a scene photographically, strong interest in numbers, recalling travel routes, knowing country flags and currency instantly.",
            "scoring_pattern": "Common protocol for intense interests."
        },
        "order_number": 5
    },
    {
        "id": "9c131116-bf25-414a-8e19-dc42a1a7e18c",
        "section_id": "a7eb6907-b791-4874-b0d1-f646f1515ea4",
        "text": "Does the child attempt to comfort others who are upset?",
        "min_age_months": 0,
        "max_age_months": 60,
        "age_protocol": {
            "example": "0–24m: crawls/walks toward crying sibling. 25–36m: shares toy/eatable to comfort. 37–60m: hugs, invites peer to play, shares chocolate, may say 'sorry' verbally.",
            "scoring_pattern": "Three-tier scoring – 0–24m, 25–36m, 37–60m."
        },
        "order_number": 8
    },
    {
        "id": "ad628014-501e-4335-8fe7-98e6d9e021fb",
        "section_id": "51ac875c-3011-48ac-84e0-2e5817bbf8ba",
        "text": "Does the child show atypical responses to movement?",
        "min_age_months": 12,
        "max_age_months": 60,
        "age_protocol": {
            "example": "Fear of swings or craving movement, fear of heights, fear of uneven/unbalanced surfaces.",
            "scoring_pattern": "Common protocol for vestibular responses."
        },
        "order_number": 14
    },
    {
        "id": "aec36be6-c519-4f3d-b8ee-80f079d1601e",
        "section_id": "ccdaae62-69b7-4770-ba54-77e138c5ad24",
        "text": "Does the child demonstrate age-appropriate self-care?",
        "min_age_months": 20,
        "max_age_months": 60,
        "age_protocol": {
            "example": "Washing hands independently, wearing slippers, brushing teeth with little support.",
            "scoring_pattern": "Common protocol for basic self-care."
        },
        "order_number": 6
    },
    {
        "id": "b024079f-ecd7-42a0-a21a-f3c6b37d669b",
        "section_id": "51ac875c-3011-48ac-84e0-2e5817bbf8ba",
        "text": "Does the child seek excessive sensory stimulation?",
        "min_age_months": 12,
        "max_age_months": 60,
        "age_protocol": {
            "example": "Constant jumping, pacing inside house, climbing and jumping all day, staying outdoors for long duration.",
            "scoring_pattern": "Common protocol for sensory-seeking."
        },
        "order_number": 11
    },
    {
        "id": "b25a1744-6969-4db1-98bb-e85d287663cb",
        "section_id": "f3622868-5fc1-42b0-8a8c-eead3cdb3efc",
        "text": "Does the child understand and answer WH‐questions?",
        "min_age_months": 30,
        "max_age_months": 60,
        "age_protocol": {
            "example": "Answers questions like: Where is grandmother? Who is talking to you? What is your favorite game and why? Who is your best friend? Which vehicle do you take to school? Who drops you? Favorite teacher?",
            "scoring_pattern": "Applicable 30–60 months."
        },
        "order_number": 9
    },
    {
        "id": "bcc07e38-d210-45a7-8001-a9983d94250e",
        "section_id": "ccdaae62-69b7-4770-ba54-77e138c5ad24",
        "text": "Can the child adapt to new environments?",
        "min_age_months": 24,
        "max_age_months": 60,
        "age_protocol": {
            "example": "Adjusting to a hotel stay, visiting relatives' homes, traveling to a new city.",
            "scoring_pattern": "Common protocol for environmental adaptation."
        },
        "order_number": 7
    },
    {
        "id": "c78bf907-66a2-4461-9f11-b6e46b96ae65",
        "section_id": "f3622868-5fc1-42b0-8a8c-eead3cdb3efc",
        "text": "Does the child use gestures or words to communicate needs?",
        "min_age_months": 10,
        "max_age_months": 60,
        "age_protocol": {
            "example": "10–20m: dragging parent to kitchen/fridge for hunger, pointing to stomach, saying mumum or yummy; pulling to bed for sleep. 21–30m: using single words/phrases for hunger, sleep, pain. 31–60m: using sentences like 'I am angry because you didn't get me a toy' or expressing cold, emotional usage.",
            "scoring_pattern": "Age‐specific scoring for 10–20m, 21–30m, 31–60m."
        },
        "order_number": 1
    },
    {
        "id": "c9e1daec-ae68-48d5-b1fc-e79aaddd08d3",
        "section_id": "51ac875c-3011-48ac-84e0-2e5817bbf8ba",
        "text": "Does the child show reduced sensitivity?",
        "min_age_months": 12,
        "max_age_months": 60,
        "age_protocol": {
            "example": "High tolerance to pain, sound, touch, unaware of food around mouth while eating.",
            "scoring_pattern": "Common protocol for hyposensitivity."
        },
        "order_number": 10
    },
    {
        "id": "dbeb30b5-72de-4b00-953c-422d82ed8a8e",
        "section_id": "f3622868-5fc1-42b0-8a8c-eead3cdb3efc",
        "text": "Does the child follow a simple command given by the parent?",
        "min_age_months": 10,
        "max_age_months": 60,
        "age_protocol": {
            "example": "Commands like sit down, give me, bring this, stop it, go back, let's play.",
            "scoring_pattern": "Common protocol for simple commands."
        },
        "order_number": 3
    },
    {
        "id": "dc1ac5ab-aa5a-45e4-b694-8189a3b70c1d",
        "section_id": "f3622868-5fc1-42b0-8a8c-eead3cdb3efc",
        "text": "Does the child use functional communication to solve problems?",
        "min_age_months": 36,
        "max_age_months": 60,
        "age_protocol": {
            "example": "Asks help to get food/toy, explains if fought with friend, complains about naughty classmate, negotiates with parent for a toy or dress, requests friend to search missing items at school.",
            "scoring_pattern": "Applicable 36–60 months."
        },
        "order_number": 10
    },
    {
        "id": "e02d446e-4da7-4fca-956a-9b4125ee4dbc",
        "section_id": "51ac875c-3011-48ac-84e0-2e5817bbf8ba",
        "text": "Does the child get upset when routines change?",
        "min_age_months": 12,
        "max_age_months": 60,
        "age_protocol": {
            "example": "Upset if door is closed by someone else, if food is served by another person, if park time is skipped, insisting on same sequence like fan first then light.",
            "scoring_pattern": "Common protocol for routine rigidity."
        },
        "order_number": 3
    },
    {
        "id": "e1772346-d3dc-4535-b620-21674c3b10ad",
        "section_id": "f3622868-5fc1-42b0-8a8c-eead3cdb3efc",
        "text": "Does the child use gestures naturally (waving, nodding, gesture‐based communication)?",
        "min_age_months": 10,
        "max_age_months": 60,
        "age_protocol": {
            "example": "Uses gestures like waving hands, nodding head for no, expressing meaning through gestures.",
            "scoring_pattern": "Common protocol."
        },
        "order_number": 6
    },
    {
        "id": "e478eefe-69d7-461b-a9aa-8e10e5a529b6",
        "section_id": "470926f1-81b7-46ea-a98d-29a695616a21",
        "text": "Does the child engage in purposeful play with toys?",
        "min_age_months": 24,
        "max_age_months": 60,
        "age_protocol": {
            "example": "Using a car for pretend play, racing, or pushing to ride.",
            "scoring_pattern": "Common protocol for purposeful toy play."
        },
        "order_number": 1
    },
    {
        "id": "e7c6b86b-2b63-4bc9-b1a5-47154ff1ed62",
        "section_id": "51ac875c-3011-48ac-84e0-2e5817bbf8ba",
        "text": "Is the child overly sensitive to sensory input?",
        "min_age_months": 12,
        "max_age_months": 60,
        "age_protocol": {
            "example": "Oversensitivity to sounds, textures, or bright light.",
            "scoring_pattern": "Common protocol for hypersensitivity."
        },
        "order_number": 9
    },
    {
        "id": "ead77594-21ab-42c8-9aa5-5bbd11719d6d",
        "section_id": "51ac875c-3011-48ac-84e0-2e5817bbf8ba",
        "text": "Does the child use repetitive or scripted speech?",
        "min_age_months": 12,
        "max_age_months": 60,
        "age_protocol": {
            "example": "Repeating sentences from rhymes, movies, stories, long cartoon dialogues.",
            "scoring_pattern": "Common protocol for echolalia."
        },
        "order_number": 7
    },
    {
        "id": "f575821b-a45f-4f5c-83c1-1338d71ffdfa",
        "section_id": "f3622868-5fc1-42b0-8a8c-eead3cdb3efc",
        "text": "Does the child repeat words or phrases after you while you talk?",
        "min_age_months": 8,
        "max_age_months": 30,
        "age_protocol": {
            "example": "Reciprocal sounds like tatata, thathatha, papapa, ummm; tries to repeat sounds, words, or short phrases after the parent.",
            "scoring_pattern": "Applicable 8–30 months."
        },
        "order_number": 7
    }
]


async def seed_questions():
    """
    Seed assessment questions into the database.
    This will insert or update questions based on their ID and verify section mappings.
    """
    logger.info("🌱 Starting questions seed...")
    
    async with async_session() as db:
        try:
            from sqlalchemy import select
            
            created_count = 0
            updated_count = 0
            skipped_count = 0
            missing_sections = set()
            
            # First, verify all sections exist
            logger.info("🔍 Verifying section existence...")
            section_ids = {q["section_id"] for q in QUESTIONS_DATA}
            for section_id in section_ids:
                result = await db.execute(
                    select(AssessmentSection).where(AssessmentSection.id == section_id)
                )
                section = result.scalars().first()
                if not section:
                    missing_sections.add(section_id)
                    logger.warning(f"⚠️  Section {section_id} does not exist in database!")
            
            if missing_sections:
                logger.error(f"❌ Cannot proceed: {len(missing_sections)} required sections are missing!")
                logger.error("   Please run seed_sections.py first to create the sections.")
                return
            
            logger.info("✅ All required sections found. Proceeding with questions...")
            
            # Process each question
            for question_data in QUESTIONS_DATA:
                # Check if question already exists
                result = await db.execute(
                    select(AssessmentQuestion).where(AssessmentQuestion.id == question_data["id"])
                )
                existing_question = result.scalars().first()
                
                if existing_question:
                    # Update existing question
                    logger.info(f"📝 Question '{question_data['text'][:50]}...' already exists, updating...")
                    existing_question.section_id = question_data["section_id"]
                    existing_question.text = question_data["text"]
                    existing_question.min_age_months = question_data["min_age_months"]
                    existing_question.max_age_months = question_data["max_age_months"]
                    existing_question.age_protocol = question_data["age_protocol"]
                    existing_question.order_number = question_data["order_number"]
                    updated_count += 1
                else:
                    # Create new question
                    logger.info(f"✨ Creating question: {question_data['text'][:50]}...")
                    new_question = AssessmentQuestion(
                        id=question_data["id"],
                        section_id=question_data["section_id"],
                        text=question_data["text"],
                        min_age_months=question_data["min_age_months"],
                        max_age_months=question_data["max_age_months"],
                        age_protocol=question_data["age_protocol"],
                        order_number=question_data["order_number"]
                    )
                    db.add(new_question)
                    created_count += 1
            
            # Commit all changes
            await db.commit()
            
            logger.info("=" * 70)
            logger.info(f"✅ Questions seeding completed!")
            logger.info(f"   📦 Created: {created_count}")
            logger.info(f"   🔄 Updated: {updated_count}")
            logger.info(f"   ⏭️  Skipped: {skipped_count}")
            logger.info("=" * 70)
            
            # Display summary by section
            logger.info("\n📋 Questions by section:")
            result = await db.execute(
                select(AssessmentSection).order_by(AssessmentSection.order_number)
            )
            sections = result.scalars().all()
            
            for section in sections:
                # Count questions for this section
                result = await db.execute(
                    select(AssessmentQuestion)
                    .where(AssessmentQuestion.section_id == section.id)
                    .order_by(AssessmentQuestion.order_number)
                )
                questions = result.scalars().all()
                
                logger.info(f"\n   📂 [{section.order_number}] {section.title}")
                logger.info(f"      Total questions: {len(questions)}")
                
                # Show first 3 questions as preview
                for i, q in enumerate(questions[:3], 1):
                    logger.info(f"      {i}. {q.text[:60]}..." if len(q.text) > 60 else f"      {i}. {q.text}")
                
                if len(questions) > 3:
                    logger.info(f"      ... and {len(questions) - 3} more questions")
            
        except Exception as e:
            logger.error(f"❌ Error seeding questions: {e}")
            await db.rollback()
            raise
        finally:
            await db.close()


async def main():
    """Main entry point"""
    try:
        await seed_questions()
    except Exception as e:
        logger.error(f"Failed to seed questions: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
