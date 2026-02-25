#!/usr/bin/env node
// ---------------------------------------------------------------------------
// test_classify.js — Stress-test the classifyQuery heuristic against 100 queries
//
// Usage: node frontend/test_classify.js
//
// Each query has an expected type. The heuristic only returns simple/complex/agent,
// so "medium" expectations map to "complex" (the intended demo behavior).
// ---------------------------------------------------------------------------

function classifyQuery(text) {
  const lower = text.toLowerCase();
  if (lower.includes('calculate') || lower.includes('how many'))
    return 'agent';
  if (lower.includes('compare') || lower.includes('versus') || lower.includes(' vs ')
      || lower.includes('analyze') || lower.includes('implications')
      || text.length > 80
      || (lower.includes(' and ') && text.length > 50))
    return 'complex';
  return 'simple';
}

// Map expected human type to heuristic bucket
// (medium → complex because we only have 3 mock response profiles)
function normalize(type) {
  return type === 'medium' ? 'complex' : type;
}

const TEST_QUERIES = [
  // === THE 10 ORIGINAL EXAMPLE QUERIES ===
  { q: "What are the base RISC-V integer instruction formats?", expect: "simple" },
  { q: "How does the RISC-V weak memory ordering model work?", expect: "simple" },
  { q: "What standard extensions are available in RISC-V?", expect: "simple" },
  { q: "Explain RISC-V privilege levels", expect: "simple" },
  { q: "What is the RISC-V vector extension and what operations does it support?", expect: "medium" },
  { q: "How does RISC-V handle privilege levels and memory protection?", expect: "medium" },
  { q: "Compare RISC-V PMP versus ARM TrustZone security models in terms of hardware isolation, privilege levels, and side-channel resistance", expect: "complex" },
  { q: "Analyze the performance implications of RISC-V vector extension vs ARM SVE for ML workloads", expect: "complex" },
  { q: "How many registers does RV32I define, and what is 2^5?", expect: "agent" },
  { q: "Analyze the RISC-V instruction decoder function and calculate the number of supported formats", expect: "agent" },

  // === SIMPLE: short factual questions ===
  { q: "What is RISC-V?", expect: "simple" },
  { q: "List the base integer ISAs", expect: "simple" },
  { q: "What does CSR stand for?", expect: "simple" },
  { q: "Describe M-mode", expect: "simple" },
  { q: "How many privilege modes exist?", expect: "agent" },  // "how many" → agent
  { q: "What is the PC register?", expect: "simple" },
  { q: "Explain compressed instructions", expect: "simple" },
  { q: "What is RV64I?", expect: "simple" },
  { q: "Define trap delegation", expect: "simple" },
  { q: "What is the ECALL instruction?", expect: "simple" },
  { q: "Describe the fence instruction", expect: "simple" },
  { q: "What is an ISA extension?", expect: "simple" },
  { q: "Explain atomic memory operations", expect: "simple" },
  { q: "What is the ABI calling convention?", expect: "simple" },
  { q: "How does branch prediction work?", expect: "simple" },
  { q: "What is a load-store architecture?", expect: "simple" },
  { q: "Describe the JALR instruction", expect: "simple" },
  { q: "What does RV32E provide?", expect: "simple" },
  { q: "Explain the RVWMO model", expect: "simple" },
  { q: "What is a hart?", expect: "simple" },

  // === COMPLEX: comparison, analysis, long queries ===
  { q: "Compare RISC-V and ARM interrupt handling", expect: "complex" },
  { q: "Compare the cache coherence protocols used in RISC-V multicore systems", expect: "complex" },
  { q: "Analyze RISC-V page table walk performance under heavy TLB miss rates", expect: "complex" },
  { q: "What are the implications of removing branch delay slots in RISC-V?", expect: "complex" },
  { q: "RISC-V vs x86 for embedded systems", expect: "complex" },
  { q: "RISC-V versus MIPS in educational settings", expect: "complex" },
  { q: "Analyze the trade-offs between hardware and software floating point in RISC-V", expect: "complex" },
  { q: "What are the security implications of PMP granularity choices?", expect: "complex" },
  { q: "Compare supervisor and machine mode exception handling in RISC-V versus ARM exception levels", expect: "complex" },
  { q: "Analyze the impact of the RISC-V compressed instruction extension on code density and instruction cache utilization", expect: "complex" },
  { q: "What are the implications of RISC-V's modular ISA approach for hardware verification?", expect: "complex" },
  { q: "Discuss how RISC-V vector extension compares to traditional SIMD approaches in terms of programmability and performance scalability", expect: "complex" },
  { q: "Analyze the power consumption trade-offs between RV32E and RV32I for IoT sensor nodes", expect: "complex" },
  { q: "FENCE.TSO vs standard FENCE: what are the ordering implications?", expect: "complex" },
  { q: "Compare the debug specification of RISC-V with ARM CoreSight for trace-based debugging", expect: "complex" },
  { q: "Explain the trade-offs between Sv39 and Sv48 virtual memory and their implications for large-memory workloads", expect: "complex" },
  { q: "How do custom RISC-V extensions interact with the standard extension naming convention and binary compatibility?", expect: "complex" },
  { q: "Analyze memory ordering guarantees of AMO instructions vs LR/SC sequences in multiprocessor RISC-V systems", expect: "complex" },
  { q: "What are the implications of not having a condition code register in RISC-V for compiler optimization?", expect: "complex" },
  { q: "Compare PLIC versus CLIC interrupt controllers for real-time RISC-V applications with strict latency requirements", expect: "complex" },

  // === COMPLEX: " and " compound with length > 50 ===
  { q: "Explain privilege levels and memory protection in RISC-V", expect: "complex" },
  { q: "Describe the vector extension and its register grouping", expect: "complex" },
  { q: "How do PMP and virtual memory work together in RISC-V?", expect: "complex" },
  { q: "Explain the M extension and the F extension differences", expect: "complex" },
  { q: "What is the relationship between harts and hardware threads in RISC-V?", expect: "complex" },

  // === COMPLEX: length > 80 (no keywords but long) ===
  { q: "Provide a detailed explanation of the RISC-V physical memory protection mechanism and its configuration", expect: "complex" },
  { q: "Describe in detail how the RISC-V trap mechanism works from the hardware perspective during an exception", expect: "complex" },
  { q: "Walk me through the entire process of a RISC-V system transitioning from M-mode to S-mode to U-mode step by step", expect: "complex" },

  // === AGENT: computational queries ===
  { q: "Calculate the maximum addressable memory in RV64I", expect: "agent" },
  { q: "How many CSRs are defined in the privileged specification?", expect: "agent" },
  { q: "Calculate the instruction encoding for ADDI x1, x0, 42", expect: "agent" },
  { q: "How many bits does the immediate field in a U-type instruction have?", expect: "agent" },
  { q: "Calculate the address range covered by one PMP entry with NAPOT granularity of 4KB", expect: "agent" },
  { q: "How many general-purpose registers are in RV32E?", expect: "agent" },
  { q: "Calculate the maximum vector length for VLEN=256 and SEW=32", expect: "agent" },
  { q: "How many page table entries fit in one 4KB page for Sv39?", expect: "agent" },
  { q: "Calculate the branch offset range for B-type instructions", expect: "agent" },
  { q: "How many interrupt sources can PLIC support?", expect: "agent" },

  // === EDGE CASES: potential misclassifications ===
  // "what is" should NOT trigger agent (was the original bug)
  { q: "What is the purpose of the MISA register?", expect: "simple" },
  { q: "What is the difference between RISC-V and CISC architectures?", expect: "complex" },  // " and " + len 61 > 50 — this is actually a comparison question
  { q: "What is an extension?", expect: "simple" },

  // "analyze" in a short query
  { q: "Analyze the RISC-V ISA", expect: "complex" },

  // " and " but short (< 50 chars) — should stay simple
  { q: "Load and store instructions", expect: "simple" },
  { q: "M and F extensions", expect: "simple" },
  { q: "Read and write CSRs", expect: "simple" },

  // " and " at exactly 50 chars (boundary)
  { q: "Explain memory ordering and fence instructions?", expect: "simple" },  // 48 chars
  { q: "Explain the memory ordering and fence instruction!", expect: "simple" },  // 50 chars — not > 50

  // " vs " in short query (should still trigger complex)
  { q: "RV32I vs RV64I", expect: "complex" },
  { q: "PMP vs TrustZone", expect: "complex" },

  // "versus" in short query
  { q: "RISC-V versus ARM", expect: "complex" },

  // No keywords, right at length boundary
  { q: "Explain the detailed mechanism of the RISC-V physical memory protection system implementation", expect: "complex" },  // 93 chars > 80

  // Exactly 80 chars — should be simple (threshold is > 80)
  { q: "Explain the detailed mechanism of the RISC-V physical memory protection system.", expect: "simple" },  // 80 chars

  // 80 chars — still simple (threshold is > 80, not >= 80)
  { q: "Explain the detailed mechanism of the RISC-V physical memory protection systems.", expect: "simple" },  // 80 chars exactly

  // Combined triggers
  { q: "Compare and analyze the RISC-V vector extension approaches", expect: "complex" },
  { q: "Calculate how many registers are needed and analyze the encoding space", expect: "agent" },  // "calculate" checked first → agent

  // Tricky: "how many" + "compare" — agent wins (checked first)
  { q: "How many cores support RISC-V compare and branch?", expect: "agent" },

  // "implications" alone
  { q: "What are the implications of RISC-V modularity?", expect: "complex" },

  // Freeform user input style
  { q: "risc-v pmp", expect: "simple" },
  { q: "help me understand interrupts", expect: "simple" },
  { q: "I want to know about the vector extension and how it handles element widths and register grouping in practice", expect: "complex" },  // " and " + > 50 + > 80
  { q: "can you calculate the total encoding space for R-type instructions?", expect: "agent" },
];

// --- Run ---
let pass = 0;
let fail = 0;
const failures = [];

for (const { q, expect } of TEST_QUERIES) {
  const got = classifyQuery(q);
  const expected = normalize(expect);
  if (got === expected) {
    pass++;
  } else {
    fail++;
    failures.push({ query: q, expected: `${expect}→${expected}`, got, len: q.length });
  }
}

const total = pass + fail;
console.log(`\n  classifyQuery heuristic test: ${pass}/${total} passed (${(pass/total*100).toFixed(1)}%)\n`);

if (failures.length > 0) {
  console.log('  FAILURES:');
  console.log('  ' + '-'.repeat(90));
  for (const f of failures) {
    console.log(`  [${f.got.padEnd(7)}] expected ${f.expected.padEnd(18)} len=${String(f.len).padStart(3)}  "${f.query}"`);
  }
  console.log();
}

process.exit(fail > 0 ? 1 : 0);
