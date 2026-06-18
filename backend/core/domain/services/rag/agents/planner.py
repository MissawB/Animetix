import logging

from core.domain.entities.ai_schemas import SearchPlan
from core.domain.services.llm_service import LLMService
from core.domain.services.prompt_manager import PromptManager

logger = logging.getLogger("animetix.rag.planner")


class SearchPlanner:
    """Agent responsable de l'analyse de la requête et de la planification de la recherche."""

    def __init__(self, llm_service: LLMService, prompt_manager: PromptManager):
        self.llm_service = llm_service
        self.prompt_manager = prompt_manager

    def plan(
        self,
        query: str,
        memories: str = "",
        thinking_budget: int = 0,
        thinking_mode: bool = False,
    ) -> SearchPlan:
        plan_prompt, plan_sys = self.prompt_manager.get_prompt(
            "searcher_plan", query=query
        )
        if memories:
            plan_sys += f"\nContexte utilisateur : {memories}"

        try:
            # 1. Tentative de génération structurée robuste avec auto-retry intégré
            plan_obj = self.llm_service.generate_structured(
                plan_prompt, SearchPlan, system_prompt=plan_sys, use_slm=True
            )

            # Normalisation robuste des entités
            if plan_obj.entities:
                cleaned_entities = []
                for ent in plan_obj.entities:
                    if isinstance(ent, dict):
                        if "name" in ent:
                            cleaned_entities.append(str(ent["name"]))
                        elif "value" in ent:
                            cleaned_entities.append(str(ent["value"]))
                        else:
                            cleaned_entities.append(str(ent))
                    else:
                        cleaned_entities.append(str(ent))
                plan_obj.entities = cleaned_entities

            # Normalisation robuste des étapes de graphe
            if plan_obj.graph_traversal_steps:
                cleaned_steps = []
                for step in plan_obj.graph_traversal_steps:
                    if isinstance(step, list):
                        for sub in step:
                            cleaned_steps.append(str(sub))
                    elif isinstance(step, dict):
                        if "relation" in step:
                            cleaned_steps.append(str(step["relation"]))
                        elif "name" in step:
                            cleaned_steps.append(str(step["name"]))
                        else:
                            cleaned_steps.append(str(step))
                    else:
                        cleaned_steps.append(str(step))
                plan_obj.graph_traversal_steps = cleaned_steps

            return plan_obj

        except Exception as err:
            logger.warning(
                f"Structured plan generation failed ({err}), falling back to manual generation..."
            )

            # 2. Repli de secours : génération textuelle classique et parsing manuel résilient
            plan_raw = self.llm_service.generate(
                plan_prompt,
                plan_sys,
                use_slm=True,
                thinking_budget=thinking_budget,
                thinking_mode=thinking_mode,
            )

            try:
                import json  # noqa: E402
                import re  # noqa: E402

                from core.domain.exceptions import ParsingError  # noqa: E402

                clean_raw = plan_raw.strip()
                if "```" in clean_raw:
                    match = re.search(
                        r"```(?:json)?\s*(\{.*?\})\s*```",
                        clean_raw,
                        re.DOTALL | re.IGNORECASE,
                    )
                    if match:
                        clean_raw = match.group(1)

                first_curly = clean_raw.find("{")
                last_curly = clean_raw.rfind("}")
                if first_curly != -1 and last_curly != -1:
                    json_str = clean_raw[first_curly : last_curly + 1]
                else:
                    json_str = clean_raw

                # Basic cleaning
                json_str = re.sub(r"//.*?\n", "\n", json_str)
                json_str = re.sub(r"/\*.*?\*/", "", json_str, flags=re.DOTALL)
                json_str = re.sub(r",\s*([\]}])", r"\1", json_str)
                json_str = re.sub(r"[\x00-\x1F\x7F]", "", json_str)

                try:
                    data = json.loads(json_str)
                except Exception as parse_err:
                    try:
                        import orjson  # noqa: E402

                        data = orjson.loads(json_str)
                    except Exception:
                        raise ParsingError(f"Failed to parse JSON: {parse_err}")

                if not isinstance(data, dict):
                    raise ParsingError("Parsed JSON is not a dictionary.")

                # Normalize entities: convert structured dictionaries to flat strings
                if "entities" in data and isinstance(data["entities"], list):
                    cleaned_entities = []
                    for ent in data["entities"]:
                        if isinstance(ent, dict):
                            if "name" in ent:
                                cleaned_entities.append(str(ent["name"]))
                            elif "value" in ent:
                                cleaned_entities.append(str(ent["value"]))
                            else:
                                cleaned_entities.append(str(ent))
                        else:
                            cleaned_entities.append(str(ent))
                    data["entities"] = cleaned_entities

                # Normalize graph_traversal_steps: convert structured lists/dicts/sublists to flat strings
                if "graph_traversal_steps" in data and isinstance(
                    data["graph_traversal_steps"], list
                ):
                    cleaned_steps = []
                    for step in data["graph_traversal_steps"]:
                        if isinstance(step, list):
                            for sub in step:
                                cleaned_steps.append(str(sub))
                        elif isinstance(step, dict):
                            if "relation" in step:
                                cleaned_steps.append(str(step["relation"]))
                            elif "name" in step:
                                cleaned_steps.append(str(step["name"]))
                            else:
                                cleaned_steps.append(str(step))
                        else:
                            cleaned_steps.append(str(step))
                    data["graph_traversal_steps"] = cleaned_steps

                return SearchPlan(**data)
            except Exception as e:
                logger.warning(f"Plan parsing failed: {e}.")
                if not isinstance(e, ParsingError):
                    raise ParsingError(f"Plan structure invalid: {str(e)}")
                raise
