"""
Configuration management system for the modular RAG pipeline.

This module provides a type-safe configuration system using Pydantic
for validation and YAML for storage. It supports multiple environments,
configuration inheritance, and ComponentFactory validation.
"""

from typing import Dict, Any, Optional, List
import yaml
from pathlib import Path
from pydantic import BaseModel, Field, field_validator, ConfigDict, model_validator
import os


class ComponentConfig(BaseModel):
    """Configuration for a single component.
    
    Attributes:
        type: Component type identifier (e.g., 'hybrid_pdf', 'sentence_transformer')
        config: Component-specific configuration parameters
    """
    type: str
    config: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        """Ensure type is not empty."""
        if not v or not v.strip():
            raise ValueError("Component type cannot be empty")
        return v.strip()


class PipelineConfig(BaseModel):
    """Complete pipeline configuration.
    
    Defines all components needed for a functional RAG pipeline.
    Supports both legacy (Phase 1) and unified (Phase 2) architectures.
    Includes ComponentFactory validation for Phase 3.
    """
    document_processor: ComponentConfig
    embedder: ComponentConfig
    vector_store: Optional[ComponentConfig] = None  # Optional in Phase 2 unified architecture
    retriever: ComponentConfig
    answer_generator: ComponentConfig
    
    # Optional global settings
    global_settings: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(extra='forbid')  # Prevent unknown fields
    
    @model_validator(mode='after')
    def validate_component_types(self):
        """Validate component types using ComponentFactory."""
        # Import here to avoid circular imports
        try:
            from .component_factory import ComponentFactory
            
            # Create configuration dict for factory validation
            config_dict = {
                'document_processor': {
                    'type': self.document_processor.type,
                    'config': self.document_processor.config
                },
                'embedder': {
                    'type': self.embedder.type,
                    'config': self.embedder.config
                },
                'retriever': {
                    'type': self.retriever.type,
                    'config': self.retriever.config
                },
                'answer_generator': {
                    'type': self.answer_generator.type,
                    'config': self.answer_generator.config
                }
            }
            
            # Add vector_store if present (optional for unified architecture)
            if self.vector_store is not None:
                config_dict['vector_store'] = {
                    'type': self.vector_store.type,
                    'config': self.vector_store.config
                }
            
            # Use factory validation
            errors = ComponentFactory.validate_configuration(config_dict)
            
            if errors:
                error_message = "Component validation failed:\n" + "\n".join(f"  - {error}" for error in errors)
                raise ValueError(error_message)
                
        except ImportError:
            # ComponentFactory not available - skip validation
            # This allows config to work during early development
            pass
        
        return self
    
    @model_validator(mode='after')
    def validate_architecture_consistency(self):
        """Validate architecture consistency (legacy vs unified)."""
        
        retriever_type = self.retriever.type
        has_vector_store = self.vector_store is not None
        
        if retriever_type == "unified":
            # Unified architecture - vector_store should be None
            if has_vector_store:
                raise ValueError(
                    "Unified retriever architecture detected, but vector_store is configured. "
                    "For unified architecture, remove the vector_store section - "
                    "the retriever handles vector storage internally."
                )
        elif retriever_type == "hybrid":
            # Legacy architecture - vector_store is required
            if not has_vector_store:
                raise ValueError(
                    "Legacy hybrid retriever architecture detected, but vector_store is missing. "
                    "For legacy architecture, configure a vector_store section, "
                    "or switch to 'unified' retriever type."
                )
        
        return self


class ConfigManager:
    """Manages configuration loading, validation, and environment handling.
    
    Supports:
    - Loading from YAML files
    - Environment variable overrides
    - Configuration inheritance
    - Validation using Pydantic
    """
    
    def __init__(self, config_path: Optional[Path] = None, env: Optional[str] = None):
        """Initialize configuration manager.
        
        Args:
            config_path: Path to configuration file
            env: Environment name (e.g., 'dev', 'test', 'prod')
        """
        self.config_path = config_path
        self.env = env or os.getenv('RAG_ENV', 'default')
        self._config: Optional[PipelineConfig] = None
        self._raw_config: Optional[Dict[str, Any]] = None
    
    def load(self) -> PipelineConfig:
        """Load and validate configuration.
        
        Returns:
            Validated pipeline configuration
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If configuration is invalid
        """
        if self.config_path and self.config_path.exists():
            return self._load_from_file(self.config_path)
        
        # Try to find config based on environment
        config_dir = Path(__file__).parent.parent.parent / "config"
        env_config = config_dir / f"{self.env}.yaml"
        
        if env_config.exists():
            return self._load_from_file(env_config)
        
        # Fall back to default config
        default_config = config_dir / "default.yaml"
        if default_config.exists():
            return self._load_from_file(default_config)
        
        # If no config file found, return a minimal default
        return self._get_default_config()
    
    def _load_from_file(self, path: Path) -> PipelineConfig:
        """Load configuration from YAML file.
        
        Args:
            path: Path to YAML file
            
        Returns:
            Validated configuration
        """
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        
        self._raw_config = data
        
        # Apply environment variable overrides
        data = self._apply_env_overrides(data)
        
        # Validate and return
        return PipelineConfig(**data)
    
    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides to configuration.
        
        Environment variables should be prefixed with RAG_ and use
        double underscores for nesting. For example:
        RAG_EMBEDDER__CONFIG__MODEL_NAME=all-MiniLM-L6-v2
        
        Args:
            config: Base configuration dictionary
            
        Returns:
            Configuration with overrides applied
        """
        import copy
        config = copy.deepcopy(config)
        
        for key, value in os.environ.items():
            if key.startswith('RAG_') and key != 'RAG_ENV':
                # Remove prefix and split by double underscore
                path_parts = key[4:].lower().split('__')
                
                # Navigate to the correct position in config
                current = config
                for i, part in enumerate(path_parts[:-1]):
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                
                # Set the value
                final_key = path_parts[-1]
                
                # Try to parse as JSON for complex types
                try:
                    import json
                    current[final_key] = json.loads(value)
                except:
                    # If not JSON, treat as string
                    # Convert 'true'/'false' to boolean
                    if value.lower() == 'true':
                        current[final_key] = True
                    elif value.lower() == 'false':
                        current[final_key] = False
                    else:
                        current[final_key] = value
        
        return config
    
    def _get_default_config(self) -> PipelineConfig:
        """Return a minimal default configuration.
        
        This is used when no configuration files are found.
        """
        return PipelineConfig(
            document_processor=ComponentConfig(
                type="hybrid_pdf",
                config={
                    "chunk_size": 1024,
                    "chunk_overlap": 128
                }
            ),
            embedder=ComponentConfig(
                type="sentence_transformer",
                config={
                    "model_name": "sentence-transformers/multi-qa-MiniLM-L6-cos-v1",
                    "use_mps": True
                }
            ),
            vector_store=ComponentConfig(
                type="faiss",
                config={
                    "index_type": "IndexFlatIP",
                    "normalize": True
                }
            ),
            retriever=ComponentConfig(
                type="hybrid",
                config={
                    "dense_weight": 0.7,
                    "sparse_weight": 0.3,
                    "top_k": 5
                }
            ),
            answer_generator=ComponentConfig(
                type="adaptive",
                config={
                    "enable_adaptive_prompts": True,
                    "enable_chain_of_thought": False,
                    "confidence_threshold": 0.85,
                    "max_tokens": 512
                }
            )
        )
    
    @property
    def config(self) -> PipelineConfig:
        """Get the loaded configuration (lazy loading).
        
        Returns:
            Pipeline configuration
        """
        if self._config is None:
            self._config = self.load()
        return self._config
    
    def save(self, path: Path) -> None:
        """Save current configuration to YAML file.
        
        Args:
            path: Path to save configuration
        """
        config_dict = self.config.model_dump()
        
        with open(path, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)
    
    def get_component_config(self, component_name: str) -> ComponentConfig:
        """Get configuration for a specific component.
        
        Args:
            component_name: Name of the component
            
        Returns:
            Component configuration
            
        Raises:
            AttributeError: If component doesn't exist
        """
        return getattr(self.config, component_name)
    
    def validate(self) -> bool:
        """Validate the current configuration.
        
        Returns:
            True if valid
            
        Raises:
            ValueError: If configuration is invalid
        """
        try:
            _ = self.config
            return True
        except Exception as e:
            raise ValueError(f"Invalid configuration: {e}")


# Utility functions
def load_config(path: Optional[Path] = None, env: Optional[str] = None) -> PipelineConfig:
    """Convenience function to load configuration.
    
    Args:
        path: Optional path to config file
        env: Optional environment name
        
    Returns:
        Loaded configuration
    """
    manager = ConfigManager(path, env)
    return manager.config


def create_default_config(output_path: Path) -> None:
    """Create a default configuration file.
    
    Args:
        output_path: Path to save the default config
    """
    manager = ConfigManager()
    default_config = manager._get_default_config()
    
    config_dict = default_config.model_dump()
    
    # Add helpful comments
    config_with_comments = f"""# RAG Pipeline Configuration
# This file defines the components and settings for the RAG pipeline

# Document processor for handling input files
document_processor:
  type: "{config_dict['document_processor']['type']}"  # Options: hybrid_pdf, simple_pdf
  config:
    chunk_size: {config_dict['document_processor']['config']['chunk_size']}
    chunk_overlap: {config_dict['document_processor']['config']['chunk_overlap']}

# Embedding generator for converting text to vectors
embedder:
  type: "{config_dict['embedder']['type']}"  # Options: sentence_transformer, openai
  config:
    model_name: "{config_dict['embedder']['config']['model_name']}"
    use_mps: {str(config_dict['embedder']['config']['use_mps']).lower()}

# Vector storage backend
vector_store:
  type: "{config_dict['vector_store']['type']}"  # Options: faiss, chroma, pinecone
  config:
    index_type: "{config_dict['vector_store']['config']['index_type']}"
    normalize: {str(config_dict['vector_store']['config']['normalize']).lower()}

# Retrieval strategy
retriever:
  type: "{config_dict['retriever']['type']}"  # Options: hybrid, semantic, bm25
  config:
    dense_weight: {config_dict['retriever']['config']['dense_weight']}
    sparse_weight: {config_dict['retriever']['config']['sparse_weight']}
    top_k: {config_dict['retriever']['config']['top_k']}

# Answer generation strategy
answer_generator:
  type: "{config_dict['answer_generator']['type']}"  # Options: adaptive, simple, chain_of_thought
  config:
    enable_adaptive_prompts: {str(config_dict['answer_generator']['config']['enable_adaptive_prompts']).lower()}
    enable_chain_of_thought: {str(config_dict['answer_generator']['config']['enable_chain_of_thought']).lower()}
    confidence_threshold: {config_dict['answer_generator']['config']['confidence_threshold']}
    max_tokens: {config_dict['answer_generator']['config']['max_tokens']}

# Global settings (optional)
global_settings: {{}}
"""
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(config_with_comments)