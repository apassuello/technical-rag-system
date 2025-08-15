# Topic Customization Guide for Claude Training Prompts

## 🎯 Quick Start: How to Customize Topics

### Step 1: Choose Your Topic Focus
Each prompt now has a **TOPIC FOCUS** section at the top. Simply:

1. **Replace** the current focus with your desired topic
2. **Copy** the entire prompt to Claude
3. **Generate** 25 samples focused on your topic

### Step 2: Example Customizations

#### For Machine Learning Focus:
```markdown
## TOPIC FOCUS (CUSTOMIZE HERE)
**Current Focus**: Machine Learning & AI Systems
**Instructions**: Focus 70-80% of queries on ML topics: model training, deployment, MLOps, data pipelines, feature engineering, model monitoring, with 20-30% general technical questions.
```

#### For Cybersecurity Focus:
```markdown
## TOPIC FOCUS (CUSTOMIZE HERE)  
**Current Focus**: Cybersecurity & Information Security
**Instructions**: Focus 70-80% of queries on security topics: threat modeling, encryption, secure coding, incident response, compliance, with 20-30% related infrastructure questions.
```

#### For Fintech Focus:
```markdown
## TOPIC FOCUS (CUSTOMIZE HERE)
**Current Focus**: Financial Technology & Banking Systems  
**Instructions**: Focus 70-80% of queries on fintech topics: payment processing, regulatory compliance, risk management, blockchain, trading systems, with 20-30% general backend questions.
```

## 📊 Topic Coverage by Complexity Level

### Simple Batch Topics (Beginner-friendly):
- **Programming Basics**: Variables, functions, loops, simple data structures
- **Tool Usage**: IDEs, version control, basic command line
- **Web Basics**: HTML, CSS, simple JavaScript
- **Database Basics**: SQL fundamentals, basic queries
- **General Computing**: File management, basic networking

### Medium Batch Topics (Intermediate):
- **Framework Usage**: React, Django, Spring Boot, Express.js
- **System Integration**: APIs, databases, caching, authentication
- **Development Practices**: Testing, debugging, code organization
- **Deployment**: Docker, basic cloud services, CI/CD
- **Performance**: Optimization techniques, monitoring

### Complex Batch Topics (Expert-level):
- **System Architecture**: Microservices, distributed systems, scalability
- **Advanced Algorithms**: Machine learning, cryptography, optimization
- **Research Topics**: Novel approaches, cutting-edge technologies
- **Enterprise Concerns**: Security at scale, compliance, governance
- **Performance Engineering**: High-throughput systems, fault tolerance

## 🔄 Creating Domain-Specific Datasets

### Example: Generate ML Engineering Dataset

**Step 1**: Modify Simple Prompt
```markdown
**Current Focus**: Machine Learning Basics
- Model concepts, training/testing, basic algorithms
- Data preprocessing, feature selection
- Python ML libraries (scikit-learn, pandas)
- Model evaluation metrics
- Basic neural network concepts
```

**Step 2**: Modify Medium Prompts
```markdown  
**Current Focus**: ML Engineering & MLOps
- Model deployment and serving
- Feature stores and data pipelines
- Model monitoring and drift detection
- A/B testing for ML models
- ML infrastructure and scaling
```

**Step 3**: Modify Complex Prompt
```markdown
**Current Focus**: Advanced ML Systems
- Distributed training architectures
- Advanced optimization techniques
- ML system performance engineering
- Research-level ML problems
- Large-scale ML infrastructure
```

### Example: Generate Cybersecurity Dataset

**Step 1**: Simple Focus
```markdown
**Current Focus**: Cybersecurity Basics
- Password security, basic encryption
- Safe browsing, phishing awareness
- Basic network security concepts
- Security tools introduction
- Privacy fundamentals
```

**Step 2**: Medium Focus  
```markdown
**Current Focus**: Security Engineering
- Secure coding practices
- Authentication and authorization systems
- Vulnerability assessment and management
- Security monitoring and incident response
- Compliance frameworks (SOC2, GDPR)
```

**Step 3**: Complex Focus
```markdown
**Current Focus**: Advanced Security Architecture
- Zero-trust architecture design
- Advanced cryptographic protocols
- Threat modeling for complex systems
- Security research and novel attacks
- Large-scale security infrastructure
```

## 🛠 Advanced Customization Tips

### 1. **Mix Topics for Diversity**
```markdown
**Current Focus**: 60% Data Engineering + 40% DevOps
**Instructions**: Generate queries covering data pipelines, ETL processes, data warehousing (60%) mixed with containerization, CI/CD, infrastructure automation (40%).
```

### 2. **Industry-Specific Focus**
```markdown
**Current Focus**: Healthcare Technology
**Instructions**: Focus on HIPAA compliance, medical data processing, healthcare APIs, patient data security, medical device integration.
```

### 3. **Technology Stack Focus**
```markdown
**Current Focus**: React/Node.js Full-Stack Development
**Instructions**: Focus on React ecosystem, Node.js backend development, full-stack patterns, modern JavaScript, API design.
```

### 4. **Role-Specific Focus**
```markdown
**Current Focus**: Platform Engineering
**Instructions**: Focus on developer tooling, internal APIs, deployment platforms, developer experience, infrastructure automation.
```

## 📋 Quality Guidelines

When customizing topics:

1. **Maintain Complexity Levels**: Ensure your topic has natural simple → complex progression
2. **Keep Domain Breadth**: Include 20-30% related topics for context
3. **Use Realistic Scenarios**: Focus on practical, real-world questions
4. **Technical Accuracy**: Ensure terminology and concepts are current and correct

## 🎯 Target Use Cases

- **Specialized Training Data**: Generate domain-specific datasets for specialized RAG systems
- **Industry Applications**: Create datasets for specific industries (fintech, healthcare, e-commerce)
- **Technology Focus**: Build datasets around specific tech stacks or frameworks
- **Role-Specific Training**: Generate questions relevant to specific engineering roles

## 📁 Recommended File Naming

When generating topic-focused batches:
```
simple_batch_25_ML_basics.json
medium_batch_25_MLOps_1.json  
medium_batch_25_MLOps_2.json
complex_batch_25_advanced_ML.json
```

This makes it easy to track topic-focused datasets and combine them strategically.

## 🔄 Iterative Refinement

1. **Generate initial batch** with topic focus
2. **Review sample quality** and topic coverage
3. **Refine topic description** if needed
4. **Generate additional batches** with refined focus
5. **Combine strategically** for balanced domain coverage

The prompts are now designed for easy topic customization while maintaining all the quality controls and structure that ensure excellent training data!