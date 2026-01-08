"""
AI Service - Gemini Integration
Provides AI capabilities using Google's Gemini API

This service is instantiated as a singleton in main.py and injected via FastAPI dependencies.
Features comprehensive logging, audit trails, and token counting for cost tracking.
"""

from typing import Optional, Dict, Any, List
import json
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential
import tiktoken
import time

from app_logging.logger import get_logger
from app_logging.audit import audit_log
from config.settings import settings

logger = get_logger(__name__)


class GeminiService:
    """
    Gemini AI Service.
    Handles all interactions with Google's Gemini API with comprehensive logging and monitoring.
    """

    def __init__(self):
        """
        Initialize the Gemini service with API credentials and token encoder.
        """
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL
        self.temperature = settings.GEMINI_TEMPERATURE
        self.max_tokens = settings.GEMINI_MAX_TOKENS
        
        # Initialize tiktoken encoder for token counting
        # Using cl100k_base which is compatible with GPT-4 and similar models
        try:
            self.encoder = tiktoken.get_encoding("cl100k_base")
            logger.info("tiktoken_encoder_initialized", encoding="cl100k_base")
        except Exception as e:
            logger.warning("tiktoken_encoder_init_failed", error=str(e))
            self.encoder = None
        
        # Configure the Gemini API
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
            logger.info(
                "gemini_service_initialized",
                model=self.model_name,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                token_counting_enabled=bool(self.encoder)
            )
            
            # Audit log service initialization
            audit_log(
                event_type="ai_service_initialization",
                actor="system",
                resource="gemini_service",
                action="initialize",
                result="success",
                model=self.model_name
            )
        else:
            logger.warning(
                "gemini_api_key_missing",
                message="GEMINI_API_KEY not configured. AI features will be disabled."
            )
            self.model = None

    def is_available(self) -> bool:
        """
        Check if the Gemini service is available.
        
        Returns:
            bool: True if service is configured and ready, False otherwise
        """
        return self.model is not None

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using tiktoken.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            int: Number of tokens, or character count / 4 as fallback
        """
        if self.encoder:
            try:
                return len(self.encoder.encode(text))
            except Exception as e:
                logger.warning("token_counting_failed", error=str(e))
        
        # Fallback: approximate as chars / 4
        return len(text) // 4

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def generate_text(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_instruction: Optional[str] = None,
        actor: str = "system"
    ) -> str:
        """
        Generate text using Gemini API with comprehensive logging.
        
        Args:
            prompt: The user prompt/question
            temperature: Override default temperature (0.0-1.0)
            max_tokens: Override default max tokens
            system_instruction: Optional system instruction for the model
            actor: Actor making the request (for audit logging)
            
        Returns:
            str: Generated text response
            
        Raises:
            ValueError: If service is not available
            Exception: If API call fails after retries
        """
        if not self.is_available():
            logger.error("gemini_service_unavailable", actor=actor)
            raise ValueError("Gemini service is not configured. Please set GEMINI_API_KEY.")
        
        start_time = time.time()
        
        try:
            # Use provided values or fall back to defaults
            temp = temperature if temperature is not None else self.temperature
            max_tok = max_tokens if max_tokens is not None else self.max_tokens
            
            # Count input tokens
            prompt_tokens = self.count_tokens(prompt)
            system_tokens = self.count_tokens(system_instruction) if system_instruction else 0
            total_input_tokens = prompt_tokens + system_tokens
            
            # Configure generation parameters with strict JSON mode
            generation_config = genai.GenerationConfig(
                temperature=temp,
                max_output_tokens=max_tok,
                response_mime_type="application/json",
                # Candidate count must be 1 for JSON mode
                candidate_count=1
            )
            
            # Create model with system instruction if provided
            if system_instruction:
                model = genai.GenerativeModel(
                    self.model_name,
                    system_instruction=system_instruction
                )
            else:
                model = self.model
            
            # Log request with token counts
            logger.info(
                "gemini_generate_request",
                actor=actor,
                prompt_length=len(prompt),
                prompt_tokens=prompt_tokens,
                system_tokens=system_tokens,
                total_input_tokens=total_input_tokens,
                temperature=temp,
                max_tokens=max_tok,
                has_system_instruction=bool(system_instruction)
            )
            
            # Generate content
            response = model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            # Extract text from response
            result = response.text
            
            # Count output tokens
            output_tokens = self.count_tokens(result)
            total_tokens = total_input_tokens + output_tokens
            
            # Calculate duration
            duration_ms = round((time.time() - start_time) * 1000, 2)
            
            # Get finish reason
            finish_reason = None
            if response.candidates:
                finish_reason = str(response.candidates[0].finish_reason)
            
            # Log success with comprehensive metrics
            logger.info(
                "gemini_generate_success",
                actor=actor,
                response_length=len(result),
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                finish_reason=finish_reason,
                duration_ms=duration_ms,
                tokens_per_second=round(output_tokens / (duration_ms / 1000), 2) if duration_ms > 0 else 0
            )
            
            # Audit log AI interaction
            audit_log(
                event_type="ai_generation",
                actor=actor,
                resource="gemini_api",
                action="generate_text",
                result="success",
                model=self.model_name,
                input_tokens=total_input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                duration_ms=duration_ms,
                finish_reason=finish_reason
            )
            
            return result
            
        except Exception as e:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            
            logger.error(
                "gemini_generate_error",
                actor=actor,
                error=str(e),
                error_type=type(e).__name__,
                duration_ms=duration_ms
            )
            
            # Audit log failure
            audit_log(
                event_type="ai_generation",
                actor=actor,
                resource="gemini_api",
                action="generate_text",
                result="failure",
                error=str(e),
                error_type=type(e).__name__,
                duration_ms=duration_ms
            )
            
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )

    async def map_questions_to_answers(
        self,
        conversation: Dict[str, Any],
        questions: List[Dict[str, Any]],
        child_age_months: Optional[int] = None,
        actor: str = "system",
        custom_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Map questions to their answers from a voice conversation transcript.
        
        This function analyzes a conversation between bot and human to extract
        answers to specific questions and returns structured JSON output.
        
        Args:
            conversation: JSON object representing the voice conversation
                         Example: {
                             "messages": [
                                 {"speaker": "bot", "text": "What is your child's name?"},
                                 {"speaker": "human", "text": "His name is Alex"},
                                 ...
                             ]
                         }
            questions: List of questions to map answers for
                      Example: [
                          {"id": "q1", "question": "What is your child's name?"},
                          {"id": "q2", "question": "How old is your child?"},
                          ...
                      ]
            child_age_months: Optional child's age in months for context
            actor: Actor making the request (for audit logging)
            custom_prompt: Optional custom prompt to override the default
                          PASTE YOUR CUSTOM PROMPT HERE if needed
            
        Returns:
            Dict containing structured JSON with question-answer mappings
            Example: {
                "success": True,
                "mappings": [
                    {"question_id": "q1", "question": "...", "answer": "Alex", "confidence": "high"},
                    ...
                ],
                "raw_response": "..."
            }
        """
        if not self.is_available():
            logger.error("gemini_service_unavailable", actor=actor, operation="map_questions")
            raise ValueError("Gemini service is not configured.")
        
        start_time = time.time()
        
        # Build the prompt
        if custom_prompt:
            # Use custom prompt if provided
            prompt = custom_prompt
        else:
            # Add child age context if provided
            age_context = f"\nCHILD AGE: {child_age_months} months\n" if child_age_months else ""
            
            # Default prompt - PASTE YOUR CUSTOM PROMPT HERE TO OVERRIDE
            prompt = f"""
You are a clinical assessment reasoning engine.

Your task is to analyze a transcribed parent–clinician conversation and map
the parent's FINAL answers to the provided assessment questions.
age in months is {age_context}
This is a psychological assessment.
You MUST follow these rules strictly:
- Use only the FIRST meaningful answer per question
- Answers may be spread across multiple utterances
- Ignore repetitions, filler words, or later corrections
- Do NOT invent answers
- Do NOT rephrase answers
- Do NOT score outside the defined scoring rules

CONVERSATION TRANSCRIPT (JSON):
{json.dumps(conversation, indent=2)}

ASSESSMENT QUESTIONS (JSON):
{json.dumps(questions, indent=2)}

SCORING RULES (MANDATORY):
0 = skill absent
1 = rare / emerging (≤25%)
2 = inconsistent / needs physical or caregiver support (~50%)
3 = mostly present / verbal reminders (~75%)
4 = fully present / independent

ANSWER BUCKETS (STRICT):
YES | SOMETIMES | NO | NOT_OBSERVED

TASK:
For each question:
1. Extract the parent's final answer from the conversation
2. Normalize it into an answer_bucket
3. Assign a numeric score (0–4)
4. Provide brief clinical justification
5. If answers and questions and in any other language other than English, then translate it to English and then map it to the question.
6. If the answers are already in English then raw_answer and eng_translated_answer will be same,any of them should not be empty.
7. If parent does not answer a question and tries to skip it or ends conversation prematurely, DO NOT CONSIDER IT AS ANSWER AND DO NOT MAP IT TO ANY QUESTION.
8. Analyze the answer and check if it makes in context of the question and is a valid answer, that is if it answers the question which was asked then map it.


Return ONLY valid JSON with the EXACT structure below.


OUTPUT FORMAT (STRICT JSON):
{{
  "answers": [
    {{
      "question_id": "string",
      "raw_answer": "string",
      "eng_translated_answer": "string",
      "answer_bucket": "YES|SOMETIMES|NO|NOT_OBSERVED",
      "score": 0,
      "confidence": 0.0,
      "justification": "short clinical reasoning"
    }}
  ],
  "meta": {{
    "unanswered_question_ids": [],
    "answered_count": 0,
    "total_questions": 0,
    "completion_status": "IN_PROGRESS|COMPLETED"
  }}
}}

IMPORTANT:
- Output ONLY JSON
- Do NOT include markdown
- Do NOT include explanations outside JSON
- Every question MUST appear either in answers[] or unanswered_question_ids
"""
        
        try:
            logger.info(
                "gemini_map_questions_request",
                actor=actor,
                question_count=len(questions),
                conversation_length=len(str(conversation)),
                using_custom_prompt=bool(custom_prompt)
            )
            
            # Generate response with JSON output
            response = await self.generate_text(
                prompt=prompt,
                actor=actor,
                temperature=0.3,  # Lower temperature for more consistent JSON
                system_instruction="You are a precise data extraction assistant. Always return valid JSON."
            )
            
            # Try to parse the JSON response
            try:
                # Clean response (remove markdown code blocks if present)
                cleaned_response = response.strip()
                if cleaned_response.startswith("```json"):
                    cleaned_response = cleaned_response[7:]
                if cleaned_response.startswith("```"):
                    cleaned_response = cleaned_response[3:]
                if cleaned_response.endswith("```"):
                    cleaned_response = cleaned_response[:-3]
                cleaned_response = cleaned_response.strip()
                
                parsed_result = json.loads(cleaned_response)
                
                duration_ms = round((time.time() - start_time) * 1000, 2)
                
                logger.info(
                    "gemini_map_questions_success",
                    actor=actor,
                    question_count=len(questions),
                    mapped_count=len(parsed_result.get("mappings", [])),
                    unmapped_count=len(parsed_result.get("unmapped_questions", [])),
                    duration_ms=duration_ms
                )
                
                # Audit log
                audit_log(
                    event_type="ai_question_mapping",
                    actor=actor,
                    resource="gemini_api",
                    action="map_questions_to_answers",
                    result="success",
                    question_count=len(questions),
                    mapped_count=len(parsed_result.get("mappings", [])),
                    duration_ms=duration_ms
                )
                
                return {
                    "success": True,
                    "result": parsed_result,
                    "raw_response": response
                }
                
            except json.JSONDecodeError as e:
                logger.warning(
                    "gemini_map_questions_json_parse_error",
                    actor=actor,
                    error=str(e),
                    response_preview=response[:200]
                )
                
                # Return raw response if JSON parsing fails
                return {
                    "success": False,
                    "error": "Failed to parse JSON response",
                    "raw_response": response
                }
                
        except Exception as e:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            
            logger.error(
                "gemini_map_questions_error",
                actor=actor,
                error=str(e),
                error_type=type(e).__name__,
                duration_ms=duration_ms
            )
            
            # Audit log failure
            audit_log(
                event_type="ai_question_mapping",
                actor=actor,
                resource="gemini_api",
                action="map_questions_to_answers",
                result="failure",
                error=str(e),
                duration_ms=duration_ms
            )
            
            raise

    async def generate_assessment_summary(
        self,
        assessment_responses: List[Dict[str, Any]],
        actor: str = "system",
        custom_prompt: Optional[str] = None,
        include_recommendations: bool = True
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive AI summary after all assessments are completed.
        
        This function takes all assessment responses and generates a final summary
        with insights, patterns, and recommendations.
        
        Args:
            assessment_responses: List of all assessment responses
                                 Example: [
                                     {
                                         "assessment_id": "a1",
                                         "assessment_type": "developmental",
                                         "questions_and_answers": [...],
                                         "metadata": {...}
                                     },
                                     ...
                                 ]
            actor: Actor making the request (for audit logging)
            custom_prompt: Optional custom prompt to override the default
                          PASTE YOUR CUSTOM PROMPT HERE if needed
            include_recommendations: Whether to include recommendations in summary
            
        Returns:
            Dict containing the AI-generated summary
            Example: {
                "success": True,
                "summary": {
                    "overall_assessment": "...",
                    "key_findings": [...],
                    "developmental_insights": {...},
                    "recommendations": [...],
                    "areas_of_concern": [...],
                    "strengths": [...]
                },
                "raw_response": "..."
            }
        """
        if not self.is_available():
            logger.error("gemini_service_unavailable", actor=actor, operation="assessment_summary")
            raise ValueError("Gemini service is not configured.")
        
        start_time = time.time()
        
        # Build the prompt
        if custom_prompt:
            # Use custom prompt if provided
            prompt = custom_prompt
        else:
            # Default prompt - PASTE YOUR CUSTOM PROMPT HERE TO OVERRIDE
            recommendations_instruction = """
- Recommendations: Provide specific, actionable recommendations for parents and healthcare providers
""" if include_recommendations else ""
            
            prompt = f"""
You are a pediatric development specialist AI assistant analyzing comprehensive assessment data.

ASSESSMENT DATA:
{json.dumps(assessment_responses, indent=2)}

TASK:
Analyze all the assessment responses and generate a comprehensive summary that includes:
- Overall Assessment: High-level summary of the child's developmental status
- Key Findings: Most important observations from all assessments
- Developmental Insights: Analysis of developmental milestones and progress
{recommendations_instruction}- Areas of Concern: Any red flags or areas needing attention
- Strengths: Positive aspects and areas where the child is thriving
- Next Steps: Suggested follow-up actions

Return your response as a valid JSON object with this structure:
{{
    "overall_assessment": "comprehensive summary paragraph",
    "key_findings": [
        "finding 1",
        "finding 2",
        ...
    ],
    "developmental_insights": {{
        "cognitive": "analysis",
        "social_emotional": "analysis",
        "physical": "analysis",
        "language": "analysis"
    }},
    "recommendations": [
        "recommendation 1",
        "recommendation 2",
        ...
    ],
    "areas_of_concern": [
        "concern 1 with severity level",
        ...
    ],
    "strengths": [
        "strength 1",
        ...
    ],
    "next_steps": [
        "step 1",
        ...
    ],
    "confidence_level": "high|medium|low",
    "notes": "any additional clinical notes"
}}

IMPORTANT:
- Return ONLY valid JSON, no markdown formatting
- Be thorough but concise
- Use evidence-based developmental knowledge
- If there are any follow up questions in conversation but those follow question do not exists in questions array then map those under the root question.
- If there is any nummeric data but  written in words instead of number then convert it to number. Example three kilo -> 3 kilo
- Be sensitive and supportive in language
- Highlight both concerns and strengths
"""
        
        try:
            logger.info(
                "gemini_assessment_summary_request",
                actor=actor,
                assessment_count=len(assessment_responses),
                include_recommendations=include_recommendations,
                using_custom_prompt=bool(custom_prompt)
            )
            
            # Generate summary with structured output
            response = await self.generate_text(
                prompt=prompt,
                actor=actor,
                temperature=0.4,  # Balanced temperature for clinical accuracy with some nuance
                max_tokens=4096,  # Allow longer summaries
                system_instruction="You are a pediatric development specialist providing evidence-based, compassionate assessments. Always return valid JSON."
            )
            
            # Try to parse the JSON response
            try:
                # Clean response (remove markdown code blocks if present)
                cleaned_response = response.strip()
                if cleaned_response.startswith("```json"):
                    cleaned_response = cleaned_response[7:]
                if cleaned_response.startswith("```"):
                    cleaned_response = cleaned_response[3:]
                if cleaned_response.endswith("```"):
                    cleaned_response = cleaned_response[:-3]
                cleaned_response = cleaned_response.strip()
                
                parsed_result = json.loads(cleaned_response)
                
                duration_ms = round((time.time() - start_time) * 1000, 2)
                
                logger.info(
                    "gemini_assessment_summary_success",
                    actor=actor,
                    assessment_count=len(assessment_responses),
                    findings_count=len(parsed_result.get("key_findings", [])),
                    recommendations_count=len(parsed_result.get("recommendations", [])),
                    duration_ms=duration_ms
                )
                
                # Audit log
                audit_log(
                    event_type="ai_assessment_summary",
                    actor=actor,
                    resource="gemini_api",
                    action="generate_summary",
                    result="success",
                    assessment_count=len(assessment_responses),
                    duration_ms=duration_ms
                )
                
                return {
                    "success": True,
                    "summary": parsed_result,
                    "raw_response": response
                }
                
            except json.JSONDecodeError as e:
                logger.warning(
                    "gemini_assessment_summary_json_parse_error",
                    actor=actor,
                    error=str(e),
                    response_preview=response[:200]
                )
                
                # Return raw response if JSON parsing fails
                return {
                    "success": False,
                    "error": "Failed to parse JSON response",
                    "raw_response": response
                }
                
        except Exception as e:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            
            logger.error(
                "gemini_assessment_summary_error",
                actor=actor,
                error=str(e),
                error_type=type(e).__name__,
                duration_ms=duration_ms
            )
            
            # Audit log failure
            audit_log(
                event_type="ai_assessment_summary",
                actor=actor,
                resource="gemini_api",
                action="generate_summary",
                result="failure",
                error=str(e),
                duration_ms=duration_ms
            )
            
            raise

    async def generate_pool_summary(
        self,
        pool_data: Dict[str, Any],
        actor: str = "system"
    ) -> Dict[str, Any]:
        """
        Generate AI summary for a specific assessment pool.
        
        Args:
            pool_data: Pool data including sections, scores, and answers
                      Example: {
                          "pool_id": "uuid",
                          "pool_title": "Communication Skills",
                          "sections": [
                              {
                                  "section_title": "Social Interaction",
                                  "total_score": 15,
                                  "max_possible_score": 20,
                                  "answers": [...]
                              }
                          ]
                      }
            actor: Actor making the request (for audit logging)
            
        Returns:
            Dict containing the AI-generated summary
        """
        if not self.is_available():
            logger.error("gemini_service_unavailable", actor=actor, operation="pool_summary")
            raise ValueError("Gemini service is not configured.")
        
        start_time = time.time()
        
        # Extract applicability info to avoid f-string syntax errors
        is_applicable = pool_data.get('is_applicable', True)
        child_age = pool_data.get('child_age_months', 'N/A')
        applicability_status = "NOT APPLICABLE - Zero applicable questions for this age" if not is_applicable else "APPLICABLE"
        
        # Build task description based on applicability
        if not is_applicable:
            task_desc = f"SPECIAL CASE: This pool has ZERO applicable questions/sections for the child's age. Generate a brief summary explaining that this developmental pool is not applicable for assessment at this age and therefore NOT INCLUDED IN SCORING OR DEVELOPMENTAL ANALYSIS."
            critical_instruction = "- CRITICAL: Clearly state this pool is NOT APPLICABLE and NOT INCLUDED IN SCORING due to age"
            overview_note = " - NOT APPLICABLE for this age"
            obs_text = f"Not applicable for child aged {child_age} months - no questions in this developmental area are age-appropriate at this time."
            analysis_text = f"This developmental pool contains no age-appropriate questions for a child of {child_age} months. This pool is not evaluated at this developmental stage and is excluded from scoring and analysis."
            strengths_text = "N/A - pool not applicable for this age"
            attention_text = "None - this pool will be assessed when the child is older and questions become age-appropriate"
            score_text = "Not applicable - this pool is excluded from scoring for this age group (0 points, 0 max possible). This does not indicate a concern, only that assessment items are designed for different age ranges."
        else:
            task_desc = """Generate a comprehensive summary for this assessment pool that includes:
- Pool Overview: Brief overview of what this pool measures
- Key Observations: Most important findings from all sections in this pool
- Developmental Analysis: Analysis specific to this developmental area
- Strengths: Positive aspects observed in this pool
- Areas for Attention: Specific areas within this pool that need attention
- Overall Pool Score: If applicable, contextual meaning of the score"""
            critical_instruction = ""
            overview_note = ""
            obs_text = "observation 1, observation 2, ..."
            analysis_text = "detailed analysis of this developmental area"
            strengths_text = "strength 1, strength 2, ..."
            attention_text = "area 1 with specific recommendations, ..."
            score_text = "interpretation of the pool score if applicable"
        
        prompt = f"""
You are a pediatric development specialist AI analyzing assessment data for a specific developmental pool.

POOL DATA:
{json.dumps(pool_data, indent=2)}

CONTEXT:
- Child's age: {child_age} months
- Pool applicability: {applicability_status}
- Total sections in pool: {pool_data.get('total_sections_in_pool', len(pool_data.get('sections', [])))}
- Applicable sections: {pool_data.get('applicable_sections_count', len(pool_data.get('sections', [])))}
- Non-applicable sections: {pool_data.get('non_applicable_sections_count', 0)}

TASK:
{task_desc}

Return your response as valid JSON with this structure:
{{
    "pool_overview": "brief description of pool and what it measures{overview_note}",
    "key_observations": [
        "{obs_text}"
    ],
    "developmental_analysis": "{analysis_text}",
    "strengths": [
        "{strengths_text}"
    ],
    "areas_for_attention": [
        "{attention_text}"
    ],
    "score_interpretation": "{score_text}",
    "confidence_level": "high"
}}

IMPORTANT:
- Return ONLY valid JSON, no markdown formatting
- Be thorough but concise. Do not include any additional text.
- Keep it short and concise without losing any critical information.
- Use evidence-based developmental knowledge
- Be sensitive and supportive in language
- Focus on this specific pool's developmental area

CRITICAL JSON SAFETY RULES:
- DO NOT use apostrophes anywhere (child's → child, don't → do not)
- DO NOT use contractions (can't → cannot, won't → will not)
- DO NOT use possessive forms (write "the child" instead of "child's")
- Use simple, clear language without special punctuation
- Avoid quotation marks within your text
- Write full words, never shortened forms

{critical_instruction}
"""
        
        try:
            logger.info(
                "gemini_pool_summary_request",
                actor=actor,
                pool_id=pool_data.get("pool_id"),
                pool_title=pool_data.get("pool_title")
            )
            
            response = await self.generate_text(
                prompt=prompt,
                actor=actor,
                temperature=0.4,
                max_tokens=8192,  # Increased for large pools like Onboarding
                system_instruction="You are a pediatric development specialist. You MUST return ONLY valid JSON. Never use apostrophes, contractions, or possessive forms in your text. Write full words only."
            )
            
            # Parse JSON response
            try:
                cleaned_response = response.strip()
                if cleaned_response.startswith("```json"):
                    cleaned_response = cleaned_response[7:]
                if cleaned_response.startswith("```"):
                    cleaned_response = cleaned_response[3:]
                if cleaned_response.endswith("```"):
                    cleaned_response = cleaned_response[:-3]
                cleaned_response = cleaned_response.strip()
                
                parsed_result = json.loads(cleaned_response)
                
                duration_ms = round((time.time() - start_time) * 1000, 2)
                
                logger.info(
                    "gemini_pool_summary_success",
                    actor=actor,
                    pool_id=pool_data.get("pool_id"),
                    duration_ms=duration_ms
                )
                
                audit_log(
                    event_type="ai_pool_summary",
                    actor=actor,
                    resource="gemini_api",
                    action="generate_pool_summary",
                    result="success",
                    pool_id=pool_data.get("pool_id"),
                    duration_ms=duration_ms
                )
                
                return {
                    "success": True,
                    "summary": parsed_result,
                    "raw_response": response
                }
                
            except json.JSONDecodeError as e:
                logger.warning(
                    "gemini_pool_summary_json_parse_error",
                    actor=actor,
                    error=str(e),
                    response_preview=response[:200]
                )
                
                # Try to sanitize the JSON
                try:
                    sanitized = response
                    
                    # Remove any markdown code blocks
                    if "```json" in sanitized:
                        sanitized = sanitized.split("```json")[1].split("```")[0].strip()
                    elif "```" in sanitized:
                        sanitized = sanitized.split("```")[1].split("```")[0].strip()
                    
                    # Use json_repair to fix malformed JSON
                    try:
                        from json_repair import repair_json
                        sanitized = repair_json(sanitized)
                        parsed_result = json.loads(sanitized)
                        
                        logger.info(
                            "gemini_pool_summary_repaired_success",
                            actor=actor,
                            pool_id=pool_data.get("pool_id")
                        )
                        
                        return {
                            "success": True,
                            "summary": parsed_result,
                            "raw_response": response,
                            "was_sanitized": True
                        }
                    except ImportError:
                        # json_repair not available, try manual fix
                        logger.warning("json_repair_not_available", actor=actor)
                        
                        # Manual fix: escape unescaped quotes in string values
                        # This is a simple heuristic for common issues
                        import re
                        
                        # Fix common apostrophe issues: childs -> child's (escaped)
                        sanitized = re.sub(r'([a-z])s\s', r"\1's ", sanitized)
                        
                        parsed_result = json.loads(sanitized)
                        
                        logger.info(
                            "gemini_pool_summary_sanitized_success",
                            actor=actor,
                            pool_id=pool_data.get("pool_id")
                        )
                        
                        return {
                            "success": True,
                            "summary": parsed_result,
                            "raw_response": response,
                            "was_sanitized": True
                        }
                    
                except Exception as sanitize_error:
                    logger.error(
                        "gemini_pool_summary_sanitization_failed",
                        actor=actor,
                        original_error=str(e),
                        sanitize_error=str(sanitize_error),
                        response_preview=response[:500]
                    )
                    
                    return {
                        "success": False,
                        "error": "Failed to parse JSON response after sanitization",
                        "raw_response": response
                    }
                
        except Exception as e:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            
            logger.error(
                "gemini_pool_summary_error",
                actor=actor,
                error=str(e),
                error_type=type(e).__name__,
                duration_ms=duration_ms
            )
            
            audit_log(
                event_type="ai_pool_summary",
                actor=actor,
                resource="gemini_api",
                action="generate_pool_summary",
                result="failure",
                error=str(e),
                duration_ms=duration_ms
            )
            
            raise

    async def generate_final_report(
        self,
        pool_summaries: List[Dict[str, Any]],
        child_info: Dict[str, Any],
        actor: str = "system"
    ) -> Dict[str, Any]:
        """
        Generate comprehensive final report from all pool summaries.
        
        Args:
            pool_summaries: List of all pool summaries
                           Example: [
                               {
                                   "pool_id": "uuid",
                                   "pool_title": "Communication Skills",
                                   "summary": {...},
                                   "total_score": 45,
                                   "max_possible_score": 60
                               },
                               ...
                           ]
            child_info: Child information dict
            actor: Actor making the request (for audit logging)
            
        Returns:
            Dict containing the comprehensive final report
        """
        if not self.is_available():
            logger.error("gemini_service_unavailable", actor=actor, operation="final_report")
            raise ValueError("Gemini service is not configured.")
        
        start_time = time.time()
        
        prompt = f"""
You are a pediatric development specialist AI creating a structured clinical assessment report.

CHILD INFORMATION (NO IDENTIFYING INFORMATION PROVIDED):
{json.dumps(child_info, indent=2)}

ALL POOL SUMMARIES WITH SCORES:
{json.dumps(pool_summaries, indent=2)}

TASK:
Synthesize all provided information into a comprehensive developmental assessment report.
Use clear, clinically appropriate language that is empathetic and evidence-based.
Do NOT invent facts. Base all conclusions strictly on the provided data.

IMPORTANT: Use the placeholders {{{{child_name}}}}, {{{{father_name}}}}, and {{{{mother_name}}}} wherever names would appear.
These will be replaced by the client application after generation - DO NOT try to fill them in yourself.
You have NOT been provided with any names for privacy reasons.


------------------------
REPORT STRUCTURE
------------------------

Return ONLY valid JSON in the following exact structure:

{{
  "reasons_for_assessment_or_referral": {{
    "key_reasons": [
      "5–6 word concise reason",
      "another brief reason"
    ],
    "summary": "A short paragraph explaining why {{child_name}} was referred for assessment, based on reported concerns and observed patterns."
  }},

  "developmental_and_family_history": {{
    "birth_history": [
      "Gestation: ...",
      "Delivery: ...",
      "Perinatal Complications: ...",
      "Birth Weight: ...",
      "Prenatal Risks: ..."
    ],
    "medical_history": [
      "Relevant medical condition or absence of issues",
      "Hospitalizations or therapies if any"
    ],
    "family_history": [
      "Family history of developmental, neurological, or psychiatric conditions",
      "Environmental or genetic risk factors if reported"
    ]
  }},

  "current_functioning_parent_reported": {{
    "pools": [
      {{
        "pool_name": "Name of developmental pool",
        "observations": [
          "Clear functional observation",
          "Another important observation",
          "Behavioral or developmental note"
        ],
        "summary": "Brief narrative summary of {{child_name}}’s functioning in this domain."
      }}
    ]
  }},

  "summary_of_findings": {{
    "key_strengths": [
      "Observed developmental strength",
      "Another consistent strength"
      #Wrap this up in 4-5 points without losing any important information
    ],
    "areas_of_concern": [
      "Specific developmental concern",
      "Another area requiring support"
      #Wrap this up in 4-5 points without losing any important information
    ],
    "observed_patterns_of_autistic_features": [
      "Observed social-communication pattern",
      "Behavioral or interactional pattern"
      #Wrap this up in 4-5 points without losing any important information
    ],
    "functional_impact_on_daily_life": [
      "Impact on home routines",
      "Impact on social participation or learning"
      #Wrap this up in 4-5 points without losing any important information
    ]
  }},

  "diagnostic_consideration": {{
    "final_score": {{
      "total_score": "put numeric value of autism concerns index here",
      "max_possible_score": "Put 100 in here",
      "autism_concerns_index": "numeric value",
      "interpretation": "Low | Moderate | High concern"
    }},
    "conclusion": "Clinically reasoned conclusion summarizing developmental risk, emphasizing that this assessment is a screening tool and not a standalone diagnosis. Reference {{child_name}} and family context where appropriate."
  }}
}}

------------------------
IMPORTANT RULES
------------------------

#Scoring Rules:
- Pool weights:
    - Onboarding: 0%  
    - Social Reciprocity: 25%
    - Language and Communication: 28%
    - Adaptive Behavior and Self help: 28%
    - Cognition and Play: 19%
- Calculation of Autism Likelyhood Index:
    - Pool % Score calculation:
        - if Max Possible Score > 0: 
            - Pool % Score = (Total Score / Max Possible Score) * 100
        - else:
            - Pool is not applicable
    - normalized_weight = pool_weight / sum_of_applicable_weights 
    - Final Autism Concerns Index (ACI) = sum of all (pool scores * normalized_weights)
    - Interpretation:
        - Low concern: 0 - 30
        - Moderate concern: 31 <= ACI < 60
        - High concern: ACI >= 61

#Reporting Rules:
- Return ONLY valid JSON — no markdown, no explanations.
- Do not change the order of sections and subsections in JSON.
- Every list item MUST follow the format: "Label: Value"
- Labels should be short clinical descriptors (2–4 words).
- Values should be concise, factual, and parent-reported where applicable.
- Do NOT hard-code labels unless data supports them.
- Maintain neutral, non-alarming clinical tone.
- Balance strengths and concerns clearly.
- Do NOT provide a definitive diagnosis.

CRITICAL JSON SAFETY RULES (FOLLOW STRICTLY):
- DO NOT use apostrophes ANYWHERE (child's → child, parent's → parent)
- DO NOT use contractions (don't → do not, can't → cannot, won't → will not)
- DO NOT use possessive forms (write "the child" not "child's abilities")
- Use simple, clear language without special punctuation marks
- Avoid quotation marks within your response text
- Write full words only, never shortened or contracted forms
- Replace all apostrophes with simple alternatives before generating JSON
"""

        
        try:
            logger.info(
                "gemini_final_report_request",
                actor=actor,
                child_id=child_info.get("child_id"),
                pool_count=len(pool_summaries)
            )
            
            response = await self.generate_text(
                prompt=prompt,
                actor=actor,
                temperature=0.4,
                max_tokens=16384,
                system_instruction="You are a pediatric development specialist. You MUST return ONLY valid JSON. Never use apostrophes, contractions, or possessive forms. Write full words only."
            )
            
            # Parse JSON response
            try:
                cleaned_response = response.strip()
                if cleaned_response.startswith("```json"):
                    cleaned_response = cleaned_response[7:]
                if cleaned_response.startswith("```"):
                    cleaned_response = cleaned_response[3:]
                if cleaned_response.endswith("```"):
                    cleaned_response = cleaned_response[:-3]
                cleaned_response = cleaned_response.strip()
                
                parsed_result = json.loads(cleaned_response)
                
                duration_ms = round((time.time() - start_time) * 1000, 2)
                
                logger.info(
                    "gemini_final_report_success",
                    actor=actor,
                    child_id=child_info.get("child_id"),
                    duration_ms=duration_ms
                )
                
                audit_log(
                    event_type="ai_final_report",
                    actor=actor,
                    resource="gemini_api",
                    action="generate_final_report",
                    result="success",
                    child_id=child_info.get("child_id"),
                    duration_ms=duration_ms
                )
                
                return {
                    "success": True,
                    "summary": parsed_result,
                    "raw_response": response
                }
                
            except json.JSONDecodeError as e:
                logger.warning(
                    "gemini_final_report_json_parse_error",
                    actor=actor,
                    error=str(e),
                    response_preview=response[:200]
                )
                
                # Try to repair JSON
                try:
                    from json_repair import repair_json
                    repaired = repair_json(cleaned_response)
                    parsed_result = json.loads(repaired)
                    
                    logger.info(
                        "gemini_final_report_repaired_success",
                        actor=actor,
                        child_id=child_info.get("child_id")
                    )
                    
                    return {
                        "success": True,
                        "summary": parsed_result,
                        "raw_response": response,
                        "was_repaired": True
                    }
                except Exception as repair_error:
                    logger.error(
                        "gemini_final_report_repair_failed",
                        actor=actor,
                        original_error=str(e),
                        repair_error=str(repair_error)
                    )
                    
                    return {
                        "success": False,
                        "error": "Failed to parse JSON response after repair",
                        "raw_response": response
                    }
                
        except Exception as e:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            
            logger.error(
                "gemini_final_report_error",
                actor=actor,
                error=str(e),
                error_type=type(e).__name__,
                duration_ms=duration_ms
            )
            
            audit_log(
                event_type="ai_final_report",
                actor=actor,
                resource="gemini_api",
                action="generate_final_report",
                result="failure",
                error=str(e),
                duration_ms=duration_ms
            )
            
            raise

