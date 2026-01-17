"""
Code generator - creates actual files from AppSpecification
"""

import os
from pathlib import Path
from typing import Dict, Any, List
from agent import AppSpecification, DatabaseModel, Route, ModelField
from templates import (
    get_main_py_template,
    get_models_py_template,
    get_database_py_template,
    get_base_html_template,
    get_index_html_template,
    get_style_css_template,
    get_pyproject_toml_template,
)


class CodeGenerator:
    """Generates file structure for web applications"""
    
    def __init__(self, apps_dir: str = "apps"):
        self.apps_dir = Path(apps_dir)
        self.apps_dir.mkdir(exist_ok=True)
    
    def generate_app(self, spec: AppSpecification) -> Path:
        """
        Generate complete app from specification
        
        Args:
            spec: AppSpecification from the agent
            
        Returns:
            Path to the generated app directory
        """
        # Slugify app name for directory
        slug_name = spec.app_name.lower().strip().replace(" ", "-")
        app_dir = self.apps_dir / slug_name
        app_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (app_dir / "templates").mkdir(exist_ok=True)
        (app_dir / "static").mkdir(exist_ok=True)
        
        # Generate files
        self._generate_main_py(app_dir, spec)
        self._generate_models_py(app_dir, spec)
        self._generate_database_py(app_dir)
        self._generate_templates(app_dir, spec)
        self._generate_static(app_dir)
        self._generate_pyproject_toml(app_dir, spec)
        self._generate_readme(app_dir, spec)
        
        return app_dir
    
    def _generate_main_py(self, app_dir: Path, spec: AppSpecification):
        """Generate main.py FastAPI application"""
        # Slugify if needed
        clean_name = spec.app_name.replace("-", " ").title()
        
        # Check if AI defined its own root route
        has_ai_root = any(r.path == "/" and r.method.upper() == "GET" for r in spec.routes)
        
        root_route_code = ""
        if has_ai_root:
            root_route_code = "# Root route handled by AI in additional_routes"
        else:
            # Generate default root route
            index_logic = self._build_index_logic(spec)
            template_context = self._build_template_context(spec)
            padding = ", " if template_context else ""
            
            root_route_code = f'''@app.get("/", response_class=HTMLResponse)
async def index(request: Request, db: Session = Depends(get_db)):
    """Default index route"""
    {index_logic}
    return templates.TemplateResponse(
        "index.html",
        {{"request": request{padding}{template_context}}}
    )'''
            
        additional_routes = self._build_routes(spec)
        
        content = get_main_py_template()
        content = content.replace("{{app_name}}", clean_name)
        content = content.replace("{{app_description}}", spec.app_description)
        content = content.replace("{{root_route}}", root_route_code)
        content = content.replace("{{additional_routes}}", additional_routes)
        
        (app_dir / "main.py").write_text(content)
    
    def _generate_models_py(self, app_dir: Path, spec: AppSpecification):
        """Generate models.py database models"""
        model_definitions = self._build_models(spec.models)
        
        content = get_models_py_template().replace(
            "{{model_definitions}}", model_definitions
        )
        
        (app_dir / "models.py").write_text(content)
    
    def _generate_database_py(self, app_dir: Path):
        """Generate database.py configuration"""
        content = get_database_py_template()
        (app_dir / "database.py").write_text(content)
    
    def _generate_templates(self, app_dir: Path, spec: AppSpecification):
        """Generate Jinja2 templates"""
        templates_dir = app_dir / "templates"
        
        # base.html
        base_content = get_base_html_template().replace(
            "{{ app_name }}", 
            spec.app_name.replace('-', ' ').title()
        )
        (templates_dir / "base.html").write_text(base_content)
        
        # index.html
        index_content = get_index_html_template().replace(
            "{{content}}", spec.template_content
        )
        (templates_dir / "index.html").write_text(index_content)
        
        # Extra templates
        for template in spec.extra_templates:
            t_content = get_index_html_template().replace(
                "{{content}}", template.content
            )
            (templates_dir / template.name).write_text(t_content)
    
    def _generate_static(self, app_dir: Path):
        """Generate static files (CSS)"""
        static_dir = app_dir / "static"
        (static_dir / "style.css").write_text(get_style_css_template())
    
    def _generate_pyproject_toml(self, app_dir: Path, spec: AppSpecification):
        """Generate pyproject.toml for uv"""
        content = get_pyproject_toml_template()
        slug_name = spec.app_name.lower().strip().replace(" ", "-")
        content = content.replace("{{app_name_slug}}", slug_name)
        content = content.replace("{{app_description}}", spec.app_description)
        (app_dir / "pyproject.toml").write_text(content)

    def _generate_readme(self, app_dir: Path, spec: AppSpecification):
        """Generate README for the app"""
        readme_content = f"""# {spec.app_name.replace('-', ' ').title()}

{spec.app_description}

## Setup and Run

This project is managed by [uv](https://github.com/astral-sh/uv).

### Quick Start
```bash
uv run uvicorn main:app --reload
```

Then open your browser to http://localhost:8000

## Generated by QuickApp

This application was automatically generated using QuickApp.
"""
        (app_dir / "README.md").write_text(readme_content)
    
    def _build_index_logic(self, spec: AppSpecification) -> str:
        """Build automatic logic for index route"""
        if not spec.models:
            return "# No models to fetch"
        
        model = spec.models[0]
        return f"items = db.query(models.{model.name}).order_by(models.{model.name}.created_at.desc()).all()"

    def _build_template_context(self, spec: AppSpecification) -> str:
        """Build automatic template context"""
        if not spec.models:
            return ""
        return '"items": items'
    
    def _build_routes(self, spec: AppSpecification) -> str:
        """Build additional routes from specification"""
        routes = []
        
        for route in spec.routes:
            route_code = self._build_single_route(route, spec)
            if route_code:
                routes.append(route_code)
        
        return "\n\n".join(routes) if routes else "# No additional routes"
    
    def _build_single_route(self, route: Route, spec: AppSpecification) -> str:
        """Build an automatic route based on the specified action intent"""
        method = route.method.lower()
        path = route.path
        action = route.action.upper()
        
        # Determine target model
        target_model = None
        if route.target_model:
            target_model = next((m for m in spec.models if m.name == route.target_model), None)
        elif spec.models:
            target_model = spec.models[0]

        # 1. Action: CREATE
        if action == "CREATE" and target_model:
            form_params = []
            init_params = []
            for field in target_model.fields:
                if field.name.lower() in ['id', 'created_at']: continue
                f_type = "str" if field.type.lower() in ["string", "text"] else "int"
                form_params.append(f"{field.name}: {f_type} = Form(...)")
                init_params.append(f"{field.name}={field.name}")
            
            param_list = f"request: Request, {', '.join(form_params)}, db: Session = Depends(get_db)"
            handler_body = f"""
    item = models.{target_model.name}({', '.join(init_params)})
    db.add(item)
    db.commit()
    return RedirectResponse(url="/", status_code=303)"""

        # 2. Action: TOGGLE (Needs /path/{id})
        elif action == "TOGGLE" and target_model and route.target_field:
            field_name = route.target_field
            param_list = "request: Request, id: int, db: Session = Depends(get_db)"
            handler_body = f"""
    item = db.query(models.{target_model.name}).filter(models.{target_model.name}.id == id).first()
    if item:
        item.{field_name} = not item.{field_name}
        db.commit()
    return RedirectResponse(url="/", status_code=303)"""

        # 3. Action: DELETE (Needs /path/{id})
        elif action == "DELETE" and target_model:
            param_list = "request: Request, id: int, db: Session = Depends(get_db)"
            handler_body = f"""
    item = db.query(models.{target_model.name}).filter(models.{target_model.name}.id == id).first()
    if item:
        db.delete(item)
        db.commit()
    return RedirectResponse(url="/", status_code=303)"""

        # 4. Action: RENDER (Default)
        else:
            param_list = "request: Request, db: Session = Depends(get_db)"
            handler_body = f"""
    return templates.TemplateResponse("{route.response_template}", {{
        "request": request,
        "app_name": "{spec.app_name}"
    }})"""

        # Safe function name
        func_name = path.strip("/").split("/")[0].replace("-", "_") or "action"
        if method != 'get' or action != "RENDER":
            func_name = f"{method}_{action.lower()}_{func_name}"

        return f'''@app.{method}("{path}")
async def {func_name}({param_list}):
    """{route.description}"""{handler_body}'''
    
    def _build_models(self, models: List[DatabaseModel]) -> str:
        """Build SQLAlchemy model definitions"""
        if not models:
            return "# No models defined"
        
        model_code = []
        for model in models:
            model_code.append(self._build_single_model(model))
        
        return "\n\n".join(model_code)
    
    def _build_single_model(self, model: DatabaseModel) -> str:
        """Build a single SQLAlchemy model"""
        name = model.name
        table_name = model.table_name or (name.lower() + 's')
        fields = model.fields
        
        # Build fields
        field_lines = [
            "    id = Column(Integer, primary_key=True, index=True)"
        ]
        
        for field in fields:
            field_name = field.name
            # Skip if field is 'id' to avoid overwriting our primary key
            if field_name.lower() == 'id':
                continue
                
            field_type = field.type
            nullable = field.nullable
            
            field_line = f"    {field_name} = Column({field_type}"
            if not nullable:
                field_line += ", nullable=False"
            field_line += ")"
            field_lines.append(field_line)
        
        # Add timestamp
        field_lines.append("    created_at = Column(DateTime(timezone=True), server_default=func.now())")
        
        return f'''class {name}(Base):
    __tablename__ = "{table_name}"
    
{chr(10).join(field_lines)}
'''
