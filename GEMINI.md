# GEMINI.md

This file establishes the operating principles for the Gemini AI assistant (Antigravity) within the `braintrain` repository.

## 🚀 Core Directives

### 1. Minimalist Code Reviews
*   **Token Efficiency**: Reduce verbose descriptions. Prioritize code snippets and brief annotations.
*   **No Redundancy**: Do not reiterate what the code obviously does. Focus on *why* and *risk*.

### 2. Code Review Graph (Efficiency Mode)
When performing reviews, use a "Graph-Style" summary to visualize impacts and changes quickly:

**Structure:**
- **[File/Component]** → **[Change/Risk]** → **[Downstream Effect]**

**Example:**
- `UserAuth.ts` → `Added token refresh` → `Fixes session timeout bug`
- `HeaderNew.tsx` → `Props change` → `Update Home navigation logic`

### 3. Execution Preferences
*   **Direct Implementation**: Favor implementation over extensive planning documents unless the task is architecturally complex.
*   **LGTM Protocol**: If the code is correct and follows repository patterns, provide a brief "LGTM" rather than a summary of correctness.
*   **Error Reporting**: Report errors as: `Location` -> `Error` -> `Fix`.

## 🛠 Repository Context
*   **Stack**: This is a monorepo (`pnpm`) using Vite/Next.js/React.
*   **Patterns**: Follow existing design systems and navigation patterns established in `packages/` or `apps/`.
