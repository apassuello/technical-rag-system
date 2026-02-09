"""Golden corpus for validation testing.

Three RISC-V paragraphs with known content, plus one off-topic document
for negative testing. Each golden case maps a query to the expected
top-1 document and grounding keywords.
"""

RISCV_OVERVIEW = (
    "RISC-V is an open standard instruction set architecture based on "
    "established reduced instruction set computer principles. Unlike most "
    "other ISA designs, RISC-V is provided under royalty-free open-source "
    "licenses. RISC-V was originally designed in 2010 at the University of "
    "California, Berkeley. The project was led by Krste Asanovic and David "
    "Patterson. The RISC-V foundation was established to maintain the "
    "standard and promote adoption across the semiconductor industry."
)

RISCV_EXTENSIONS = (
    "RISC-V supports a modular set of extensions. The base integer ISA is "
    "named RV32I for 32-bit and RV64I for 64-bit address spaces. Standard "
    "extensions include M for integer multiplication and division, A for "
    "atomic instructions, F for single-precision floating-point, D for "
    "double-precision floating-point, and C for compressed instructions. "
    "The vector extension V enables SIMD-style parallel data processing. "
    "Custom extensions can be added for domain-specific acceleration in "
    "areas such as machine learning, cryptography, and signal processing."
)

RISCV_APPLICATIONS = (
    "RISC-V processors are used in embedded systems, high-performance "
    "computing, and edge devices. Western Digital has deployed over one "
    "billion RISC-V cores in storage controllers. SiFive produces RISC-V "
    "cores for commercial applications. In the automotive sector, RISC-V "
    "is being adopted for safety-critical ADAS systems. The architecture "
    "is also popular in academic research and teaching, where its open "
    "nature allows students to study and modify the processor design."
)

OFF_TOPIC_WEATHER = (
    "The weather forecast for Zurich shows temperatures between 2 and 8 "
    "degrees Celsius with occasional rain showers throughout the week. "
    "Snow is expected above 1200 meters elevation in the Alps region."
)

# Each case: query -> expected top-1 doc index, grounding keywords
GOLDEN_RETRIEVAL_CASES = [
    {
        "query": "What is RISC-V?",
        "expected_top1_index": 0,  # RISCV_OVERVIEW
        "grounding_terms": ["open standard", "instruction set", "Berkeley"],
    },
    {
        "query": "What extensions does RISC-V support?",
        "expected_top1_index": 1,  # RISCV_EXTENSIONS
        "grounding_terms": ["RV32I", "vector extension", "floating-point"],
    },
    {
        "query": "Where are RISC-V processors used in industry?",
        "expected_top1_index": 2,  # RISCV_APPLICATIONS
        "grounding_terms": ["Western Digital", "SiFive", "embedded"],
    },
]

ALL_CORPUS_TEXTS = [RISCV_OVERVIEW, RISCV_EXTENSIONS, RISCV_APPLICATIONS, OFF_TOPIC_WEATHER]
ON_TOPIC_TEXTS = [RISCV_OVERVIEW, RISCV_EXTENSIONS, RISCV_APPLICATIONS]
