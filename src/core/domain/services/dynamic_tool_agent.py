import logging
import ast
import traceback
from typing import Dict, Any, List, Set
from core.ports.inference_port import InferencePort
from .prompt_manager import PromptManager

logger = logging.getLogger("animetix.agent")

class CodeSafetyValidator(ast.NodeVisitor):
    """
    AST validator to ensure generated code is safe.
    """
    ALLOWED_MODULES = {"requests", "json", "math", "datetime", "re"}

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
            if node.func.id in {"eval", "exec", "open", "input", "getattr", "setattr", "delattr", "help", "copyright", "credits", "license"}:
                self.errors.append(f"Call to function '{node.func.id}' forbidden.")
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        # Block access to ALL attributes starting with _
        if node.attr.startswith("_"):
            self.errors.append(f"Access to private/internal attribute '{node.attr}' forbidden.")
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name):
        # Block access to internal identifiers
        if node.id.startswith("__") and node.id != "__name__":
             self.errors.append(f"Access to internal identifier '{node.id}' forbidden.")
        self.generic_visit(node)

class DynamicToolAgent:
    """
    Agent capable of creating its own tools.
    """
    def __init__(self, inference_engine: InferencePort, prompt_manager: PromptManager):
        self.inference_engine = inference_engine
        self.prompt_manager = prompt_manager

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

        logger.info("💻 Generated Code:")
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
            }
        }
        local_scope = {}

        try:
            # Execute the function definition with restricted globals
            exec(generated_code, restricted_globals, local_scope)

            if 'execute_tool' not in local_scope:
                return {"status": "error", "error": "Function 'execute_tool' not defined by the LLM."}

            # Execute the generated tool
            logger.info("🚀 Executing dynamic tool...")
            result = local_scope['execute_tool']()
            return {"status": "success", "data": result}

        except Exception as e:
            error_msg = traceback.format_exc()
            logger.error(f"❌ Dynamic Tool Execution Failed: {e}")
            return {"status": "error", "error": str(e), "traceback": error_msg}
