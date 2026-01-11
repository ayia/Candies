# QA VALIDATION REPORT - Intent Extraction System
**Date:** 2026-01-11
**Test Suite:** Comprehensive Intent Extraction Validation (55 tests)
**Status:** ❌ **FAILED - CRITICAL ISSUES FOUND**

---

## Executive Summary

The automated QA validation suite has identified **critical failures** in the intent extraction system. While the core LLM-based approach is working, there are significant issues with object extraction, NSFW classification, and action detection that prevent the system from meeting acceptance criteria.

### Overall Results
- **Pass Rate:** 49.1% (27/55 tests) ❌
- **Required Pass Rate:** ≥85%
- **Gap:** -35.9 percentage points
- **Average Score:** 0.771/1.0 ✅ (meets ≥0.70 threshold)

### Verdict
**❌ ACCEPTANCE CRITERIA NOT MET**

The system requires significant improvements before production deployment.

---

## Results by Category

| Category | Pass Rate | Tests Passed | Average Score | Status |
|----------|-----------|--------------|---------------|--------|
| **NSFW Detection** | 10.0% | 1/10 | 0.544 | ❌ CRITICAL |
| **Location Detection** | 30.0% | 3/10 | 0.769 | ❌ MAJOR |
| **Simple Objects** | 50.0% | 5/10 | 0.783 | ❌ NEEDS IMPROVEMENT |
| **Edge Cases** | 66.7% | 2/3 | 0.769 | ⚠️ BORDERLINE |
| **Actions** | 70.0% | 7/10 | 0.861 | ⚠️ ACCEPTABLE |
| **Multiple Objects** | 70.0% | 7/10 | 0.862 | ⚠️ ACCEPTABLE |
| **Complex Scenarios** | 100.0% | 2/2 | 0.935 | ✅ EXCELLENT |

---

## Critical Test Results

### ✅ Key Tests That PASSED

**Test #21: Sucking Lollipop (THE ORIGINAL USER PROBLEM)**
- **Request:** "Envoie moi une photo de toi en train de sucer une sucette"
- **Score:** 0.92/1.0 ✅
- **Status:** PASSED
- **Analysis:** The core problem that started this entire implementation is now SOLVED. The system correctly extracts:
  - Objects: ["colorful lollipop candy"]
  - Action: "sucking lollipop with tongue visible"
  - NSFW Level: 1 (suggestive)

**Test #31: Classroom Teacher**
- **Request:** "Photo sexy de toi en prof dans ta classe"
- **Score:** 0.96/1.0 ✅
- **Status:** PASSED
- **Analysis:** Successfully extracts:
  - Objects: ["glasses", "teacher desk", "blackboard"]
  - Action: "standing confidently"
  - Location: "classroom with blackboard"
  - NSFW Level: 1

**Test #51: Complex Multi-Element**
- **Request:** "Photo de toi dans ta chambre au lit avec un livre et un café"
- **Score:** 0.92/1.0 ✅
- **Status:** PASSED
- **Analysis:** Handles complex requests with multiple objects, action, and location.

---

## ❌ Critical Failures Requiring Immediate Attention

### 1. NSFW Detection - CRITICAL FAILURE (10% pass rate)

**Problem:** System cannot extract clothing-related objects and misclassifies NSFW levels.

**Failed Tests:**

| Test ID | Request | Expected Objects | Got Objects | Expected NSFW | Got NSFW |
|---------|---------|------------------|-------------|---------------|----------|
| #42 | "Photo sexy en lingerie" | ["lingerie"] | ["none specified"] | 1 | 1 |
| #45 | "Show me in a tiny bikini" | ["bikini"] | ["sunglasses", "beach towel"] | 1-2 | 1 |
| #47 | "Photo in a tight dress" | ["dress"] | [] | 1 | 1 |
| #48 | "Photo en pyjama" | ["pajamas"] | ["pyjamas", "possibly a book"] | 0 | 0 |
| #49 | "Photo with wet shirt" | ["shirt"] | ["beach balls", "sunglasses"] | 1 | 1 |
| #39 | "Photo de toi dans ta chambre au lit" | - | - | 0 | **4** ❌ |
| #50 | "Photo sous la douche" | ["shower"] | ["shower curtain", "soap"] | 2 | **4** ❌ |

**Root Causes:**
1. **Clothing items not detected as objects** - "lingerie", "bikini", "dress" are not being extracted
2. **NSFW over-classification** - Innocent bedroom/shower scenes getting NSFW level 4 instead of 0-2
3. **Context confusion** - Adding random objects that weren't mentioned

**Impact:** HIGH - Cannot handle sexy/flirty requests with specific clothing

---

### 2. Location Detection - MAJOR FAILURE (30% pass rate)

**Problem:** Missing implied objects and inferring wrong actions for location-based requests.

**Failed Tests:**

| Test ID | Request | Expected Location | Got Location | Issue |
|---------|---------|-------------------|--------------|-------|
| #36 | "Bathroom mirror selfie" | bathroom | bathroom | Missing objects: ["phone", "mirror"] |
| #37 | "Photo professionnelle au bureau" | office | office | Got wrong objects: ["pen", "papers"] instead of ["desk", "computer"] |
| #40 | "Coffee shop photo with a latte" | cafe | coffee shop | Action wrong: "serving" instead of "sitting" |
| #30 | "Show me you lying down relaxed" | bed | None | Location not inferred from "lying down" |

**Root Causes:**
1. **Missing implied objects** - "bathroom mirror selfie" should infer phone + mirror
2. **Action inference errors** - "coffee shop photo" assumes "serving" instead of "sitting"
3. **Location not inferred from context** - "lying down" should imply bed/couch

**Impact:** MEDIUM - Location-based requests don't get proper context

---

### 3. Simple Object Extraction - MODERATE FAILURE (50% pass rate)

**Problem:** Inconsistent extraction of single objects and their associated actions.

**Failed Tests:**

| Test ID | Request | Expected Action | Got Action | Score |
|---------|---------|-----------------|------------|-------|
| #1 | "Envoie moi une photo de toi avec une sucette" | "holding" | "posing with" | 0.67 |
| #3 | "Une photo avec des lunettes" | "wearing" | "posing or looking..." | 0.75 |
| #4 | "Show me a selfie with your phone" | "holding" | "taking selfie" | 0.58 |
| #7 | "Montre moi une photo avec un verre de vin" | "holding" | "not specified (default: posing)" | 0.58 |
| #10 | "Show me a photo wearing a necklace" | "wearing" | "posing" | 0.67 |

**Root Causes:**
1. **Action inference inconsistency** - "avec une sucette" should imply "holding", not "posing with"
2. **Wearing vs holding confusion** - Glasses and necklaces should be "wearing", not "posing"
3. **Default action overuse** - Too many requests defaulting to generic "posing"

**Impact:** MEDIUM - Single-object requests don't get precise actions

---

### 4. Action Detection - BORDERLINE (70% pass rate)

**Problem:** Missing specific action keywords in final prompts.

**Failed Tests:**

| Test ID | Request | Missing Keywords | Score |
|---------|---------|------------------|-------|
| #24 | "Send me a photo blowing a kiss" | ["blowing kiss", "hand"] | 0.78 |
| #26 | "Photo of you laughing" | ["smiling", "happy"] | 0.78 |
| #30 | "Show me you lying down relaxed" | ["lying", "bed"] | 0.58 |

**Root Causes:**
1. **Action extracted but not in final prompt** - LLM extracts "blowing kiss" but it doesn't appear in the generated prompt
2. **Keyword propagation failure** - Data flow issue between extraction and prompt generation

**Impact:** LOW-MEDIUM - Actions detected but not fully reflected in prompts

---

## Technical Analysis

### What's Working ✅

1. **LLM-Based Extraction Core** - The multi-agent system correctly understands user intent
2. **Complex Scenarios** - Handles multi-element requests (100% pass rate)
3. **Multi-language Support** - French and English both work
4. **Data Flow** - Custom details propagate through the pipeline (verified in Tests #21, #31)

### What's NOT Working ❌

1. **Clothing Object Extraction** - Cannot extract "lingerie", "bikini", "dress", "pajamas", "shirt"
2. **NSFW Level Calibration** - Over-classifies innocent scenes as NSFW 4
3. **Implied Object Inference** - Doesn't infer obvious objects (phone in "selfie", mirror in "bathroom mirror selfie")
4. **Action Consistency** - Inconsistent handling of "holding" vs "wearing" vs "posing"
5. **Keyword Propagation** - Some extracted data not making it to final prompts

---

## Root Cause Hypothesis

Based on the failure patterns, the issues appear to be in the **IntentionAnalyzer's SYSTEM_PROMPT** at [services/image_prompt_agents.py:134-210](services/image_prompt_agents.py#L134-L210):

### Issue 1: Clothing Not Treated as Objects
The prompt may not be instructing the LLM to extract clothing items as "objects".

**Current behavior:**
- Request: "Photo sexy en lingerie"
- Extracted objects: ["none specified"]
- **Expected:** ["lingerie"]

### Issue 2: NSFW Over-Classification
The NSFW level determination may be too aggressive.

**Current behavior:**
- Request: "Photo de toi dans ta chambre au lit" (innocent bedroom photo)
- NSFW Level: 4 (hardcore)
- **Expected:** 0 (SFW)

### Issue 3: Missing Inference Rules
The LLM is not inferring obvious objects from context.

**Current behavior:**
- Request: "Bathroom mirror selfie"
- Objects: []
- **Expected:** ["phone", "mirror"]

---

## Recommended Fixes (Priority Order)

### 🔴 CRITICAL - Fix 1: Update IntentionAnalyzer SYSTEM_PROMPT

**File:** [services/image_prompt_agents.py:134-210](services/image_prompt_agents.py#L134-L210)

**Changes Needed:**

1. **Add clothing to objects definition:**
```python
OBJECTS: [comma-separated list of physical objects AND clothing mentioned:
  - Physical items: lollipop, book, phone, glasses, coffee, etc.
  - Clothing items: lingerie, bikini, dress, shirt, pajamas, etc.
  - NONE if nothing specific]
```

2. **Clarify NSFW levels with examples:**
```python
NSFW_LEVEL EXAMPLES:
- 0 (SFW): "cute photo", "photo in bedroom reading", "casual photo"
- 1 (Suggestive): "sexy photo", "lingerie", "seductive pose", "tight dress"
- 2 (Explicit): "topless", "bare breasts", "nude chest"
- 3 (Hardcore): "full nude", "naked", "explicit pose"

CRITICAL: "in bedroom" does NOT automatically mean NSFW!
CRITICAL: "shower" can be SFW (clothed) or NSFW (nude) - check for nudity keywords!
```

3. **Add inference rules:**
```python
INFERENCE RULES:
- "selfie" implies phone object
- "mirror selfie" implies phone + mirror
- "bathroom mirror selfie" implies phone + mirror
- "lying down" implies bed or couch location
- "avec X" (with X) implies holding X
- "wearing X" implies X is clothing/accessory
```

### 🟠 MAJOR - Fix 2: Improve Action Detection

**File:** [services/image_prompt_agents.py:134-210](services/image_prompt_agents.py#L134-L210)

**Changes Needed:**

```python
ACTION RULES:
- "avec [object]" (with X) → "holding [object]"
- "wearing [clothing]" → "wearing [clothing]"
- "en train de [verb]" → extract the verb action
- "photo [verb]ing" → extract the verb action
- Default to "posing" ONLY if no action detected
```

### 🟡 MODERATE - Fix 3: Keyword Propagation Check

**Files to verify:**
1. [services/image_prompt_agents.py:763-783](services/image_prompt_agents.py#L763-L783) - Verify all fields returned
2. [agents/image_agent.py:131-148](agents/image_agent.py#L131-L148) - Verify propagation
3. [image_prompt_generator_v4.py:103-177](image_prompt_generator_v4.py#L103-L177) - Verify integration

**Check:** Ensure extracted actions appear in final prompt verbatim.

---

## Acceptance Criteria Status

| Metric | Threshold | Current | Status |
|--------|-----------|---------|--------|
| **Object Extraction F1** | ≥0.70 | 0.62 (estimated) | ❌ FAILED |
| **Action Precision** | ≥0.80 | 0.75 (estimated) | ❌ FAILED |
| **Location Recall** | ≥0.75 | 0.68 (estimated) | ❌ FAILED |
| **NSFW Accuracy (±1)** | ≥0.85 | 0.60 (estimated) | ❌ FAILED |
| **Semantic Consistency** | ≥0.70 | 0.77 | ✅ PASSED |
| **Overall Score** | ≥0.70 | 0.771 | ✅ PASSED |
| **Pass Rate** | ≥85% | **49.1%** | ❌ **FAILED** |

### Overall Acceptance: ❌ **FAILED**

**Gap Analysis:**
- Need to improve pass rate by **+35.9 percentage points** (from 49.1% to 85%)
- This requires fixing approximately **20 additional tests** (from 27 to 47 passed)

---

## Test Execution Details

### Test Distribution
- **Simple Objects:** 10 tests
- **Multiple Objects:** 10 tests
- **Actions:** 10 tests
- **Locations:** 10 tests
- **NSFW Levels:** 10 tests
- **Complex & Edge Cases:** 5 tests

### Language Coverage
- **French:** 27 tests (49%)
- **English:** 26 tests (47%)
- **Mixed:** 2 tests (4%)

### Execution Time
- **Total Duration:** ~8 minutes
- **Average per test:** ~9 seconds
- **Infrastructure:** Multi-agent LLM pipeline (Llama-3.1-8B via Novita AI)

---

## Conclusion

While the **core LLM-based approach is sound** and the **original user problem (lollipop test) is SOLVED**, the system has significant issues with:

1. **Clothing object extraction** (critical for NSFW/sexy requests)
2. **NSFW level calibration** (over-classifying innocent scenes)
3. **Implied object inference** (missing obvious context)
4. **Action consistency** (holding vs wearing vs posing)

These issues prevent the system from meeting the **85% pass rate** acceptance criterion.

**Recommendation:** Implement the 3 priority fixes above, then re-run the validation suite.

**Expected outcome after fixes:** Pass rate should increase from 49.1% to 80-90%, meeting acceptance criteria.

---

*Report generated: 2026-01-11*
*Test suite: test_intent_extraction_validation.py (55 tests)*
*Manual QA: manual_qa_validation.py (pending)*
