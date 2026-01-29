# app/state.py
"""
State Management for Travel Concierge Agent
Implements an 8-phase state machine for robust workflow processing.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid


class Phase(Enum):
    """Agent execution phases - 8-phase state machine."""
    Init = "Init"
    ClarifyRequirements = "ClarifyRequirements"
    PlanTools = "PlanTools"
    ExecuteTools = "ExecuteTools"
    AnalyzeResults = "AnalyzeResults"
    ResolveIssues = "ResolveIssues"
    ProduceStructuredOutput = "ProduceStructuredOutput"
    Done = "Done"


class AgentState:
    """
    Manages agent execution state through the 8-phase workflow.
    
    Phases:
    1. Init - Initialize session and capture user goal
    2. ClarifyRequirements - Ask targeted questions to gather required information
    3. PlanTools - Decide which tools to call and with what parameters
    4. ExecuteTools - Execute planned tools and collect results
    5. AnalyzeResults - Process tool outputs and validate data completeness
    6. ResolveIssues - Handle any problems or edge cases identified
    7. ProduceStructuredOutput - Generate Pydantic-validated JSON and NL summary
    8. Done - Process complete
    """
    
    # Phase transition order
    _PHASE_ORDER = [
        Phase.Init,
        Phase.ClarifyRequirements,
        Phase.PlanTools,
        Phase.ExecuteTools,
        Phase.AnalyzeResults,
        Phase.ResolveIssues,
        Phase.ProduceStructuredOutput,
        Phase.Done
    ]
    
    # Phase descriptions
    _PHASE_DESCRIPTIONS = {
        Phase.Init: "Initialize session and capture user goal",
        Phase.ClarifyRequirements: "Ask targeted questions to gather required information",
        Phase.PlanTools: "Decide which tools to call and with what parameters",
        Phase.ExecuteTools: "Execute planned tools and collect results",
        Phase.AnalyzeResults: "Process tool outputs and validate data completeness",
        Phase.ResolveIssues: "Handle any problems or edge cases identified",
        Phase.ProduceStructuredOutput: "Generate Pydantic-validated JSON and natural language summary",
        Phase.Done: "Process complete"
    }
    
    def __init__(self):
        """Initialize agent state with default values."""
        # Session metadata
        self.session_id: str = str(uuid.uuid4())
        self.created_at: datetime = datetime.utcnow()
        self.updated_at: datetime = datetime.utcnow()
        
        # Current phase
        self.phase: Phase = Phase.Init
        
        # Basic travel requirements (backward compatibility)
        self.destination: Optional[str] = None
        self.dates: Optional[str] = None
        self.card: Optional[str] = None
        
        # Enhanced requirements tracking
        self.requirements: Dict[str, Any] = {}
        self.required_fields: List[str] = []
        self.clarification_questions: List[str] = []
        
        # Tool tracking
        self.tools_called: List[str] = []
        self.tool_results: Dict[str, Any] = {}
        self.tool_errors: Dict[str, str] = {}
        
        # Analysis and validation
        self.analysis_results: Optional[Dict[str, Any]] = None
        self.data_completeness: float = 0.0
        self.validation_errors: List[str] = []
        
        # Issue tracking
        self.issues: List[str] = []
        self.resolution_attempts: List[str] = []
        self.resolved_issues: List[str] = []
        
        # Output
        self.structured_output: Optional[Dict[str, Any]] = None
        self.natural_language_summary: Optional[str] = None
        self.citations: List[str] = []
        
        # Context and metadata
        self.context: Dict[str, Any] = {}
        self.metadata: Dict[str, Any] = {}
    
    def advance(self) -> bool:
        """
        Advance to the next phase in the workflow.
        
        Returns:
            bool: True if successfully advanced, False if already at Done phase
        """
        current_index = self._PHASE_ORDER.index(self.phase)
        
        if current_index >= len(self._PHASE_ORDER) - 1:
            # Already at Done phase
            return False
        
        # Advance to next phase
        self.phase = self._PHASE_ORDER[current_index + 1]
        self._update_timestamp()
        
        return True
    
    def reset(self):
        """Reset the state to initial values for a new session."""
        # Create new session
        self.session_id = str(uuid.uuid4())
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        # Reset phase
        self.phase = Phase.Init
        
        # Reset basic requirements
        self.destination = None
        self.dates = None
        self.card = None
        
        # Reset enhanced tracking
        self.requirements = {}
        self.required_fields = []
        self.clarification_questions = []
        
        # Reset tool tracking
        self.tools_called = []
        self.tool_results = {}
        self.tool_errors = {}
        
        # Reset analysis
        self.analysis_results = None
        self.data_completeness = 0.0
        self.validation_errors = []
        
        # Reset issues
        self.issues = []
        self.resolution_attempts = []
        self.resolved_issues = []
        
        # Reset output
        self.structured_output = None
        self.natural_language_summary = None
        self.citations = []
        
        # Reset context
        self.context = {}
        self.metadata = {}
    
    def _update_timestamp(self):
        """Update the updated_at timestamp."""
        self.updated_at = datetime.utcnow()
    
    # ==================== Requirements Management ====================
    
    def set_requirements(self, requirements: Dict[str, Any]):
        """Set the requirements dictionary and update timestamp."""
        self.requirements = requirements
        
        # Also update basic fields for backward compatibility
        if "destination" in requirements:
            self.destination = requirements["destination"]
        if "dates" in requirements or "travel_dates" in requirements:
            self.dates = requirements.get("dates") or requirements.get("travel_dates")
        if "card" in requirements:
            self.card = requirements["card"]
        
        self._update_timestamp()
    
    def add_clarification_question(self, question: str):
        """Add a clarification question (avoids duplicates)."""
        if question not in self.clarification_questions:
            self.clarification_questions.append(question)
            self._update_timestamp()
    
    def mark_requirement_clarified(self, field: str):
        """Mark a required field as clarified (removes from required_fields)."""
        if field in self.required_fields:
            self.required_fields.remove(field)
            self._update_timestamp()
    
    # ==================== Tool Tracking ====================
    
    def add_tool_call(self, tool_name: str, result: Any = None, error: str = None):
        """
        Record a tool call with its result and/or error.
        
        Args:
            tool_name: Name of the tool called
            result: Result from the tool (if successful)
            error: Error message (if failed)
        """
        if tool_name not in self.tools_called:
            self.tools_called.append(tool_name)
        
        if result is not None:
            self.tool_results[tool_name] = result
        
        if error is not None:
            self.tool_errors[tool_name] = error
        
        self._update_timestamp()
    
    # ==================== Analysis ====================
    
    def set_analysis_results(self, results: Dict[str, Any]):
        """Set analysis results and calculate data completeness."""
        self.analysis_results = results
        self._calculate_data_completeness()
        self._update_timestamp()
    
    def _calculate_data_completeness(self):
        """Calculate data completeness based on required fields and requirements."""
        if not self.required_fields:
            self.data_completeness = 1.0
            return
        
        completed = sum(1 for field in self.required_fields if field in self.requirements)
        self.data_completeness = completed / len(self.required_fields) if self.required_fields else 1.0
    
    def is_data_complete(self, threshold: float = 0.8) -> bool:
        """Check if data is complete enough (default threshold: 80%)."""
        return self.data_completeness >= threshold
    
    # ==================== Issue Management ====================
    
    def add_issue(self, issue: str):
        """Add an issue to track."""
        if issue not in self.issues:
            self.issues.append(issue)
            self._update_timestamp()
    
    def add_resolution_attempt(self, attempt: str):
        """Record a resolution attempt."""
        self.resolution_attempts.append(attempt)
        self._update_timestamp()
    
    def resolve_issue(self, issue: str):
        """Mark an issue as resolved."""
        if issue in self.issues:
            self.issues.remove(issue)
            if issue not in self.resolved_issues:
                self.resolved_issues.append(issue)
            self._update_timestamp()
    
    def has_issues(self) -> bool:
        """Check if there are unresolved issues."""
        return len(self.issues) > 0
    
    # ==================== Output Management ====================
    
    def set_structured_output(self, output: Dict[str, Any], summary: str = None):
        """Set the structured output and optional natural language summary."""
        self.structured_output = output
        if summary:
            self.natural_language_summary = summary
        self._update_timestamp()
    
    def add_citation(self, citation: str):
        """Add a citation (avoids duplicates)."""
        if citation not in self.citations:
            self.citations.append(citation)
            self._update_timestamp()
    
    # ==================== Status ====================
    
    def is_complete(self) -> bool:
        """Check if the workflow is complete."""
        return self.phase == Phase.Done
    
    def get_phase_description(self) -> str:
        """Get the description of the current phase."""
        return self._PHASE_DESCRIPTIONS.get(self.phase, "Unknown phase")
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get a comprehensive status summary."""
        return {
            "session_id": self.session_id,
            "phase": self.phase.value,
            "phase_description": self.get_phase_description(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "requirements": self.requirements,
            "tools_called": self.tools_called,
            "tool_errors": list(self.tool_errors.keys()),
            "issues": self.issues,
            "resolved_issues": self.resolved_issues,
            "data_completeness": self.data_completeness,
            "has_structured_output": self.structured_output is not None,
            "citations_count": len(self.citations)
        }
    
    def __repr__(self) -> str:
        return f"AgentState(session_id={self.session_id}, phase={self.phase.value})"