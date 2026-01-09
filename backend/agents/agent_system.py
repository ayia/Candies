"""
MAIN AGENT SYSTEM (Enhanced)
Orchestrates all agents to process user messages
Based on: https://www.anthropic.com/engineering/multi-agent-research-system

Architecture:
- 4 specialized agents (removed Mood - redundant)
- Redis-persistent memory
- Full tracing for debugging
- Style consistency across conversations
"""
import asyncio
import time
from typing import Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime, timezone

from .orchestrator import OrchestratorAgent
from .conversation import ConversationAgent
from .image_agent import ImagePromptAgent
from .memory import MemoryAgent


@dataclass
class AgentConfig:
    """Configuration for each agent"""
    provider: str
    model: str


@dataclass
class TraceEvent:
    """A single trace event for debugging"""
    timestamp: str
    agent: str
    action: str
    duration_ms: float
    input_preview: str = ""
    output_preview: str = ""
    error: str = ""


@dataclass
class ProcessingTrace:
    """Full trace of message processing"""
    message_id: str
    start_time: str
    events: List[TraceEvent] = field(default_factory=list)
    total_duration_ms: float = 0


# Default agent configurations - optimized for speed and quality
DEFAULT_CONFIGS = {
    # Fast model for intent classification
    "orchestrator": AgentConfig(
        provider="novita",
        model="meta-llama/Llama-3.2-3B-Instruct"
    ),
    # Uncensored model for conversation
    "conversation": AgentConfig(
        provider="novita",
        model="Sao10K/L3-8B-Stheno-v3.2"
    ),
    # Uncensored model for image prompts (MUST be uncensored for NSFW content)
    "image": AgentConfig(
        provider="novita",
        model="Sao10K/L3-8B-Stheno-v3.2"
    ),
    # Fast model for memory operations
    "memory": AgentConfig(
        provider="novita",
        model="meta-llama/Llama-3.2-3B-Instruct"
    ),
}


class AgentSystem:
    """
    Enhanced Agent System with:
    1. 4 specialized agents (Orchestrator, Conversation, Image, Memory)
    2. Redis-persistent memory
    3. Full tracing for debugging
    4. Style consistency across conversations
    5. Parallel processing where possible

    Flow:
    1. Orchestrator analyzes intent (with keyword fallback)
    2. Memory retrieves relevant context (parallel with step 1 if possible)
    3. Conversation generates response (with style consistency)
    4. Image agent generates prompts (if needed)
    5. Memory extracts and saves new facts (background)
    """

    def __init__(
        self,
        api_key: str,
        configs: Dict[str, AgentConfig] = None,
        redis_url: str = "redis://localhost:6379",
        enable_tracing: bool = True
    ):
        self.api_key = api_key
        self.configs = configs or DEFAULT_CONFIGS
        self.enable_tracing = enable_tracing
        self.traces: List[ProcessingTrace] = []  # Keep last N traces

        # Initialize agents
        self.orchestrator = OrchestratorAgent(
            provider=self.configs["orchestrator"].provider,
            model=self.configs["orchestrator"].model,
            api_key=api_key
        )

        self.conversation = ConversationAgent(
            provider=self.configs["conversation"].provider,
            model=self.configs["conversation"].model,
            api_key=api_key
        )

        self.image_agent = ImagePromptAgent(
            provider=self.configs["image"].provider,
            model=self.configs["image"].model,
            api_key=api_key
        )

        self.memory = MemoryAgent(
            provider=self.configs["memory"].provider,
            model=self.configs["memory"].model,
            api_key=api_key,
            redis_url=redis_url
        )

        print(f"[AgentSystem] Initialized with 4 agents")
        print(f"[AgentSystem] Tracing: {'enabled' if enable_tracing else 'disabled'}")

    async def process_message(
        self,
        message: str,
        character: Dict[str, Any],
        conversation_history: List[Dict[str, str]] = None,
        character_id: int = None
    ) -> Dict[str, Any]:
        """
        Process a user message through all agents.

        Returns:
            {
                "response": str,
                "generate_image": bool,
                "image_prompt": str or None,
                "image_nsfw": bool,
                "intent": dict,
                "trace": ProcessingTrace (if tracing enabled)
            }
        """
        trace = ProcessingTrace(
            message_id=f"{character_id}_{int(time.time()*1000)}",
            start_time=datetime.now(timezone.utc).isoformat()
        )
        start_time = time.time()

        print(f"\n{'='*60}")
        print(f"[AgentSystem] Processing: {message[:50]}...")
        print(f"{'='*60}")

        # Step 1 & 2: Run orchestrator and memory retrieval in parallel
        print("[AgentSystem] Step 1-2: Intent analysis + Memory retrieval (parallel)")
        step_start = time.time()

        orchestrator_task = self.orchestrator.analyze(message)
        memory_task = self._get_memory_context(character_id, message) if character_id else asyncio.sleep(0)

        intent_data, memory_result = await asyncio.gather(
            orchestrator_task,
            memory_task,
            return_exceptions=True
        )

        # Handle exceptions
        if isinstance(intent_data, Exception):
            print(f"[AgentSystem] Orchestrator error: {intent_data}")
            intent_data = {"intent": "chat_only", "nsfw_level": 0, "emotion": "casual"}

        memory_context = ""
        user_name = None
        if isinstance(memory_result, dict):
            memory_context = memory_result.get("context", "")
            user_name = memory_result.get("user_name")
        elif isinstance(memory_result, Exception):
            print(f"[AgentSystem] Memory error: {memory_result}")

        step_duration = (time.time() - step_start) * 1000
        trace.events.append(TraceEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            agent="orchestrator+memory",
            action="parallel_analysis",
            duration_ms=step_duration,
            input_preview=message[:100],
            output_preview=f"intent={intent_data.get('intent')}, nsfw={intent_data.get('nsfw_level')}"
        ))

        print(f"[AgentSystem] Intent: {intent_data.get('intent')}, NSFW: {intent_data.get('nsfw_level')}, Source: {intent_data.get('_source', 'unknown')}")
        print(f"[AgentSystem] Memory context: {memory_context[:50]}..." if memory_context else "[AgentSystem] No memory context")
        print(f"[AgentSystem] Step 1-2 duration: {step_duration:.0f}ms")

        # Step 3: Generate conversation response
        print("[AgentSystem] Step 3: Generating response...")
        step_start = time.time()

        # Get style sample from memory if available
        style_sample = await self.memory.get_style_sample(character_id) if character_id else None

        response = await self.conversation.generate_response(
            message=message,
            character=character,
            intent_data=intent_data,
            conversation_history=conversation_history,
            memory_context=memory_context,
            style_sample=style_sample,
            user_name=user_name,
            character_id=character_id
        )

        step_duration = (time.time() - step_start) * 1000
        trace.events.append(TraceEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            agent="conversation",
            action="generate_response",
            duration_ms=step_duration,
            output_preview=response[:100] if response else "empty"
        ))

        print(f"[AgentSystem] Response: {response[:80]}..." if response else "[AgentSystem] Empty response!")
        print(f"[AgentSystem] Step 3 duration: {step_duration:.0f}ms")

        # Step 4: Generate image prompt if needed
        image_prompt = None
        generate_image = False
        image_nsfw = False
        image_nsfw_level = 0

        intent = intent_data.get("intent", "chat_only")
        if intent in ["image_request", "chat_with_image"]:
            print("[AgentSystem] Step 4: Generating image prompt with multi-agent system...")
            step_start = time.time()

            try:
                # Build conversation context for the image agents
                conv_context = ""
                if conversation_history and len(conversation_history) > 0:
                    recent = conversation_history[-4:]  # Last 4 messages
                    conv_context = "\n".join([f"{m['role']}: {m['content'][:100]}" for m in recent])

                # Get relationship level from memory if available
                relationship_level = 0
                if character_id:
                    try:
                        rel_state = await self.memory.get_relationship_level(character_id)
                        relationship_level = rel_state if rel_state else 0
                    except:
                        pass

                # Get current mood from intent
                current_mood = intent_data.get("emotion", "neutral")

                image_data = await self.image_agent.generate_image_prompt(
                    character=character,
                    intent_data=intent_data,
                    user_request=message,
                    relationship_level=relationship_level,
                    current_mood=current_mood,
                    conversation_context=conv_context
                )
                image_prompt = image_data.get("prompt", "")
                image_nsfw = image_data.get("nsfw", False)
                # Get NSFW level from multi-agent system - this is the AUTHORITATIVE source
                image_nsfw_level = image_data.get("nsfw_level", intent_data.get("nsfw_level", 0))
                generate_image = bool(image_prompt)

                step_duration = (time.time() - step_start) * 1000
                trace.events.append(TraceEvent(
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    agent="image",
                    action="generate_prompt",
                    duration_ms=step_duration,
                    output_preview=image_prompt[:100] if image_prompt else "failed"
                ))

                print(f"[AgentSystem] Image prompt: {image_prompt[:80]}..." if image_prompt else "[AgentSystem] Image prompt failed")
                print(f"[AgentSystem] Step 4 duration: {step_duration:.0f}ms")

            except Exception as e:
                print(f"[AgentSystem] Image prompt error: {e}")
                trace.events.append(TraceEvent(
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    agent="image",
                    action="generate_prompt",
                    duration_ms=0,
                    error=str(e)
                ))

        # Step 5: Background memory update (don't wait)
        if character_id and conversation_history and len(conversation_history) % 3 == 0:
            asyncio.create_task(self._update_memory(character_id, conversation_history, response))

        # Save style sample if first response
        if character_id and response and not style_sample:
            sample = response[:150].split('.')[0] + '.' if '.' in response[:150] else response[:100]
            asyncio.create_task(self.memory.save_style_sample(character_id, sample))

        # Finalize trace
        trace.total_duration_ms = (time.time() - start_time) * 1000
        if self.enable_tracing:
            self.traces.append(trace)
            # Keep only last 50 traces
            if len(self.traces) > 50:
                self.traces = self.traces[-50:]

        print(f"{'='*60}")
        print(f"[AgentSystem] Total duration: {trace.total_duration_ms:.0f}ms")
        print(f"{'='*60}\n")

        result = {
            "response": response,
            "generate_image": generate_image,
            "image_prompt": image_prompt,
            "image_nsfw": image_nsfw,
            "image_nsfw_level": image_nsfw_level,  # NSFW level from multi-agent system
            "intent": intent_data
        }

        if self.enable_tracing:
            result["trace"] = trace

        return result

    async def _get_memory_context(self, character_id: int, message: str) -> Dict[str, Any]:
        """Get memory context and user name"""
        try:
            context = await self.memory.get_relevant_context(character_id, message)
            user_name = await self.memory.get_user_name(character_id)
            return {"context": context, "user_name": user_name}
        except Exception as e:
            print(f"[AgentSystem] Memory retrieval error: {e}")
            return {"context": "", "user_name": None}

    async def _update_memory(
        self,
        character_id: int,
        conversation: List[Dict],
        latest_response: str
    ):
        """Background task to extract and store facts"""
        try:
            # Add latest exchange to conversation for analysis
            full_conv = conversation + [{"role": "assistant", "content": latest_response}]

            facts_data = await self.memory.extract_facts(full_conv)
            new_facts = facts_data.get("facts", [])

            if new_facts:
                await self.memory.save_facts(character_id, new_facts)
                print(f"[AgentSystem] Saved {len(new_facts)} facts for character {character_id}")

            # Save style sample if detected
            style_sample = facts_data.get("style_sample")
            if style_sample:
                await self.memory.save_style_sample(character_id, style_sample)

        except Exception as e:
            print(f"[AgentSystem] Memory update error: {e}")

    def get_agent_status(self) -> Dict[str, str]:
        """Get status of all agents"""
        return {
            "orchestrator": f"{self.configs['orchestrator'].provider}/{self.configs['orchestrator'].model}",
            "conversation": f"{self.configs['conversation'].provider}/{self.configs['conversation'].model}",
            "image": f"{self.configs['image'].provider}/{self.configs['image'].model}",
            "memory": f"{self.configs['memory'].provider}/{self.configs['memory'].model}",
        }

    def get_recent_traces(self, limit: int = 10) -> List[Dict]:
        """Get recent processing traces for debugging"""
        traces = self.traces[-limit:]
        return [
            {
                "message_id": t.message_id,
                "start_time": t.start_time,
                "total_duration_ms": t.total_duration_ms,
                "events": [
                    {
                        "agent": e.agent,
                        "action": e.action,
                        "duration_ms": e.duration_ms,
                        "error": e.error
                    }
                    for e in t.events
                ]
            }
            for t in traces
        ]
