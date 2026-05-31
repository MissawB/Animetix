import logging
import ast
import traceback
import concurrent.futures
from typing import Dict, Any, List, Set
from core.ports.inference_port import InferencePort
from .prompt_manager import PromptManager

logger = logging.getLogger("animetix.agent")

class CodeSafetyValidator(ast.NodeVisitor):
    """
    AST validator to ensure generated code is safe.
    """
    ALLOWED_MODULES = {"httpx", "json", "math", "datetime", "re"}
    FORBIDDEN_CALLS = {
        "eval", "exec", "open", "input", "getattr", "setattr", "delattr", "hasattr",
        "help", "copyright", "credits", "license", "dir", "vars", "locals", "globals",
        "compile", "breakpoint", "memoryview", "property", "classmethod", "staticmethod"
    }
    FORBIDDEN_ATTRS = {
        "__subclasses__", "__mro__", "__base__", "__globals__", "__builtins__", 
        "__code__", "__func__", "__self__", "__dict__", "__class__"
    }

    def __init__(self):
        self.errors = []

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            if alias.name.split('.')[0] not in self.ALLOWED_MODULES:
                self.errors.append(f"Importing module '{alias.name}' not allowed.")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module and node.module.split('.')[0] not in self.ALLOWED_MODULES:
            self.errors.append(f"Importing from module '{node.module}' not allowed.")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        # Forbidden builtins
        if isinstance(node.func, ast.Name):
            if node.func.id in self.FORBIDDEN_CALLS:
                self.errors.append(f"Call to function '{node.func.id}' forbidden.")
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        # Block access to ALL attributes starting with _ or in forbidden list
        if node.attr.startswith("_") or node.attr in self.FORBIDDEN_ATTRS:
            self.errors.append(f"Access to attribute '{node.attr}' forbidden.")
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name):
        # Block access to internal identifiers
        if node.id.startswith("__") and node.id != "__name__":
             self.errors.append(f"Access to internal identifier '{node.id}' forbidden.")
        self.generic_visit(node)

    def visit_Lambda(self, node: ast.Lambda):
        self.errors.append("Lambda functions are forbidden.")
        self.generic_visit(node)

class DynamicToolAgent:
    """
    Agent capable of creating its own tools.
    """
    def __init__(self, inference_engine: InferencePort, prompt_manager: PromptManager, timeout_seconds: int = 5):
        self.inference_engine = inference_engine
        self.prompt_manager = prompt_manager
        self.timeout_seconds = timeout_seconds

    def build_and_execute_tool(self, api_documentation: str, task: str) -> Dict[str, Any]:
        """
        Asks AI to code a tool based on doc, then executes it dynamically.
        """
        logger.info(f"🛠️ Dynamic Tool Agent: Building tool for task '{task}'...")

        prompt, system = self.prompt_manager.get_prompt(
            "dynamic_tool_builder",
            api_documentation=api_documentation,
            task=task
        )

        generated_code = self.inference_engine.generate(prompt, system_prompt=system)

        # Basic markdown cleanup
        if "```python" in generated_code:
            generated_code = generated_code.split("```python")[1].split("```")[0].strip()
        elif "```" in generated_code:
            generated_code = generated_code.split("```")[1].split("```")[0].strip()

        logger.info("💻 Generated Code (first 200 chars):")
        logger.info(generated_code[:200] + "...")

        # Safety validation
        try:
            tree = ast.parse(generated_code)
            validator = CodeSafetyValidator()
            validator.visit(tree)

            if validator.errors:
                error_msg = f"Security Violation: {', '.join(validator.errors)}"
                logger.error(f"❌ {error_msg}")
                return {"status": "error", "error": error_msg}

        except SyntaxError as e:
            return {"status": "error", "error": f"Syntax Error: {str(e)}"}

        # Dynamic execution in a restricted sandbox
        import builtins
        safe_import = builtins.__import__

        def restricted_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name.split('.')[0] in CodeSafetyValidator.ALLOWED_MODULES:
                return safe_import(name, globals, locals, fromlist, level)
            raise ImportError(f"Module '{name}' is not allowed.")

        restricted_globals = {
            "__builtins__": {
                "__import__": restricted_import,
                "print": print,
                "dict": dict,
                "list": list,
                "set": set,
                "tuple": tuple,
                "range": range,
                "len": len,
                "int": int,
                "float": float,
                "str": str,
                "bool": bool,
                "Exception": Exception,
                "ValueError": ValueError,
                "TypeError": TypeError,
                "KeyError": KeyError,
                "IndexError": IndexError,
                "StopIteration": StopIteration,
                "abs": abs,
                "round": round,
                "min": min,
                "max": max,
                "sum": sum,
                "any": any,
                "all": all,
                "enumerate": enumerate,
                "zip": zip,
            }
        }
        local_scope = {}

        try:
            # Execute the function definition with restricted globals
            exec(generated_code, restricted_globals, local_scope)

            if 'execute_tool' not in local_scope:
                return {"status": "error", "error": "Function 'execute_tool' not defined by the LLM."}

            # Execute the generated tool with timeout
            logger.info(f"🚀 Executing dynamic tool (timeout={self.timeout_seconds}s)...")
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(local_scope['execute_tool'])
                try:
                    result = future.result(timeout=self.timeout_seconds)
                    return {"status": "success", "data": result}
                except concurrent.futures.TimeoutError:
                    logger.error("❌ Dynamic Tool Execution Timed Out")
                    return {"status": "error", "error": "Execution timed out."}

        except Exception as e:
            error_msg = traceback.format_exc()
            logger.error(f"❌ Dynamic Tool Execution Failed: {e}")
            return {"status": "error", "error": str(e), "traceback": error_msg}
