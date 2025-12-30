"""LangChain-based AI Agent Microservice for Code Analysis.

This microservice receives code via HTTP requests and provides AI-powered analysis,
suggestions, and assistance using LangChain agents.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import os
from dotenv import load_dotenv
import uvicorn

from langchain_groq import ChatGroq
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_classic.tools import Tool
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from helper_agent.tools.tools import create_code_analysis_tools

load_dotenv()

app = FastAPI(
    title="AI Code Helper Service",
    description="Microservice for AI-powered code analysis and assistance",
    version="2.0.0"
)

# CORS configuration for microservice communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class CodeAnalysisRequest(BaseModel):
    code: str = Field(..., description="The code to analyze")
    language: str = Field(default="python", description="Programming language")
    query: Optional[str] = Field(None, description="Specific question or task")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    context: Optional[Dict[str, Any]] = Field(default={}, description="Additional context")

class CodeAnalysisResponse(BaseModel):
    success: bool
    response: str
    analysis: Optional[Dict[str, Any]] = None
    suggestions: Optional[List[str]] = None
    session_id: Optional[str] = None
    error: Optional[str] = None

# Initialize LangChain components
class CodeAnalysisAgent:
    def __init__(self):
        # Initialize LLM (using Groq for fast inference)
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            groq_api_key=api_key
        )
        
        # Create tools for the agent
        self.tools = create_code_analysis_tools()
        
        # Create prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are Codey, an expert AI code analysis assistant.
            
Your capabilities:
- Analyze code structure, logic, and potential issues
- Suggest improvements and optimizations
- Explain complex code patterns
- Help debug and fix errors
- Provide best practices and recommendations

When analyzing code:
1. First understand the overall structure and purpose
2. Identify key algorithms and data structures
3. Look for potential bugs, inefficiencies, or anti-patterns
4. Provide clear, actionable feedback
5. Suggest specific improvements with examples

Be concise, helpful, and provide code examples when relevant."""),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Create agent
        self.agent = create_tool_calling_agent(self.llm, self.tools, self.prompt)
        
        # Create agent executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            max_iterations=5,
            handle_parsing_errors=True
        )
        
        # Session storage (in-memory, can be replaced with Redis for production)
        self.sessions: Dict[str, List[Any]] = {}
    
    def analyze_code(self, request: CodeAnalysisRequest) -> CodeAnalysisResponse:
        """Process code analysis request."""
        try:
            # Prepare input with code and query
            if request.query:
                input_text = f"""Code to analyze:
```{request.language}
{request.code}
```

User query: {request.query}

Please analyze the code and address the user's query."""
            else:
                input_text = f"""Code to analyze:
```{request.language}
{request.code}
```

Please provide a comprehensive analysis of this code including:
1. Overall structure and purpose
2. Key algorithms and logic
3. Potential issues or bugs
4. Performance considerations
5. Suggested improvements"""
            
            # Get or create session history
            session_id = request.session_id or "default"
            chat_history = self.sessions.get(session_id, [])
            
            # Execute agent
            result = self.agent_executor.invoke({
                "input": input_text,
                "chat_history": chat_history
            })
            
            # Update session history
            chat_history.append(HumanMessage(content=input_text))
            chat_history.append(AIMessage(content=result["output"]))
            self.sessions[session_id] = chat_history[-10:]  # Keep last 10 messages
            
            return CodeAnalysisResponse(
                success=True,
                response=result["output"],
                session_id=session_id,
                analysis={
                    "language": request.language,
                    "code_length": len(request.code),
                    "lines": len(request.code.split('\n'))
                }
            )
            
        except Exception as e:
            return CodeAnalysisResponse(
                success=False,
                response="",
                error=str(e)
            )

# Initialize agent
code_agent = CodeAnalysisAgent()

@app.post("/analyze", response_model=CodeAnalysisResponse)
async def analyze_code(request: CodeAnalysisRequest):
    """Analyze code and provide AI-powered insights."""
    return code_agent.analyze_code(request)

@app.post("/chat")
async def chat_with_agent(request: CodeAnalysisRequest):
    """Interactive chat with the code analysis agent."""
    if not request.query:
        raise HTTPException(status_code=400, detail="Query is required for chat endpoint")
    return code_agent.analyze_code(request)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "AI Code Helper"}

@app.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """Clear conversation history for a session."""
    if session_id in code_agent.sessions:
        del code_agent.sessions[session_id]
        return {"success": True, "message": f"Session {session_id} cleared"}
    return {"success": False, "message": "Session not found"}

if __name__ == "__main__":
    port = int(os.getenv("AI_SERVICE_PORT", 8001))
    uvicorn.run(
        "helper_agent.agent_service:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )
