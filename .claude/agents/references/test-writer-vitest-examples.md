# test-writer — Vitest examples (extracted reference)

> Вынесено из тела агента `testing/workers/test-writer.md` 2026-08-20, чтобы не грузить системный промпт при каждом спавне.
> Примеры сняты с проекта your-app (задачи T009–T041). Читать, когда нужен точный образец мока или структуры теста.

**For Schema Validation Tests (T009, T010, T011)**:

**T009 - Style Prompts Unit Tests** - `packages/shared-types/tests/style-prompts.test.ts`:

```typescript
import { describe, it, expect, vi } from 'vitest';
import { getStylePrompt } from '../src/style-prompts';

describe('getStylePrompt', () => {
  it('should return structured prompt for valid style', () => {
    const result = getStylePrompt('minimalist');

    expect(result).toBeDefined();
    expect(result.prompt).toContain('minimalist');
    expect(result.tone).toBeDefined();
    expect(result.examples).toBeInstanceOf(Array);
  });

  it('should return default prompt for unknown style', () => {
    const result = getStylePrompt('unknown-style');

    expect(result).toBeDefined();
    expect(result.prompt).toContain('default');
  });

  it('should log warning for unknown style using Pino', () => {
    // Mock Pino logger
    const mockLogger = {
      warn: vi.fn(),
      info: vi.fn(),
      error: vi.fn(),
    };

    vi.mock('@/utils/logger', () => ({ default: mockLogger }));

    getStylePrompt('invalid-style');

    expect(mockLogger.warn).toHaveBeenCalledWith(
      expect.stringContaining('Unknown style'),
      expect.objectContaining({ style: 'invalid-style' })
    );
  });

  it('should handle all predefined styles', () => {
    const styles = ['minimalist', 'detailed', 'technical', 'creative'];

    for (const style of styles) {
      const result = getStylePrompt(style);
      expect(result.prompt).toContain(style);
    }
  });
});
```

**T010 - Generation Result Schema Tests** - `packages/shared-types/tests/generation-result.test.ts`:

```typescript
import { describe, it, expect } from 'vitest';
import { CourseStructureSchema, SectionSchema, LessonSchema } from '../src/generation/generation-result';

describe('CourseStructureSchema', () => {
  it('should validate valid course structure', () => {
    const validCourse = {
      course_title: 'Test Course',
      course_description: 'A test course',
      target_audience: 'Beginners',
      estimated_hours: 10,
      difficulty_level: 'beginner',
      prerequisites: [],
      sections: [
        {
          section_title: 'Section 1',
          section_description: 'First section',
          learning_outcomes: ['Outcome 1'],
          lessons: [
            {
              lesson_title: 'Lesson 1',
              lesson_objective: 'Learn basics',
              key_concepts: ['Concept 1'],
            },
          ],
        },
      ],
    };

    const result = CourseStructureSchema.safeParse(validCourse);
    expect(result.success).toBe(true);
  });

  it('should reject course with section missing lessons (FR-015)', () => {
    const invalidCourse = {
      course_title: 'Test Course',
      sections: [
        {
          section_title: 'Section 1',
          lessons: [], // FR-015 violation: no lessons
        },
      ],
    };

    const result = CourseStructureSchema.safeParse(invalidCourse);
    expect(result.success).toBe(false);
  });

  it('should reject invalid difficulty_level enum', () => {
    const invalidCourse = {
      course_title: 'Test Course',
      difficulty_level: 'super-hard', // Invalid enum value
    };

    const result = CourseStructureSchema.safeParse(invalidCourse);
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error.issues[0].message).toContain('difficulty_level');
    }
  });
});

describe('LessonSchema', () => {
  it('should validate valid lesson', () => {
    const validLesson = {
      lesson_title: 'Lesson 1',
      lesson_objective: 'Learn basics',
      key_concepts: ['Concept 1', 'Concept 2'],
    };

    const result = LessonSchema.safeParse(validLesson);
    expect(result.success).toBe(true);
  });

  it('should reject lesson with missing required fields', () => {
    const invalidLesson = {
      lesson_title: 'Lesson 1',
      // Missing lesson_objective
    };

    const result = LessonSchema.safeParse(invalidLesson);
    expect(result.success).toBe(false);
  });
});
```

**T011 - Generation Job Schema Tests** - `packages/shared-types/tests/generation-job.test.ts`:

```typescript
import { describe, it, expect } from 'vitest';
import { GenerationJobSchema } from '../src/generation/generation-job';

describe('GenerationJobSchema', () => {
  it('should validate title-only generation job', () => {
    const titleOnly = {
      course_title: 'Test Course',
      styles: { style_1: 'minimalist' },
      generation_mode: 'title-only',
    };

    const result = GenerationJobSchema.safeParse(titleOnly);
    expect(result.success).toBe(true);
  });

  it('should validate full Analyze generation job', () => {
    const fullAnalyze = {
      analyze_id: 'analyze_123',
      analyze_result: {
        course_title: 'Test Course',
        course_description: 'Description',
        sections: [],
      },
      styles: { style_1: 'technical' },
      generation_mode: 'full-analyze',
    };

    const result = GenerationJobSchema.safeParse(fullAnalyze);
    expect(result.success).toBe(true);
  });

  it('should reject job missing required styles', () => {
    const invalid = {
      course_title: 'Test Course',
      generation_mode: 'title-only',
      // Missing styles
    };

    const result = GenerationJobSchema.safeParse(invalid);
    expect(result.success).toBe(false);
  });
});
```

**For Service Unit Tests (T023, T024)**:

**T023 - Metadata Generator Tests** - `packages/your-app/tests/unit/metadata-generator.test.ts`:

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { generateMetadata } from '@/services/stage5/metadata-generator';
import { safeJSONParse } from '@/services/stage5/json-repair';

// Mock LLM service
vi.mock('@/services/llm/openai-service', () => ({
  callOpenAI: vi.fn(),
}));

// Mock JSON repair
vi.mock('@/services/stage5/json-repair', () => ({
  safeJSONParse: vi.fn(),
}));

describe('generateMetadata', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should generate metadata for title-only job', async () => {
    const job = {
      course_title: 'Test Course',
      styles: { style_1: 'minimalist' },
      generation_mode: 'title-only' as const,
    };

    // Mock LLM response
    const mockLLMResponse = JSON.stringify({
      course_title: 'Test Course',
      course_description: 'Generated description',
      target_audience: 'Beginners',
    });

    const { callOpenAI } = await import('@/services/llm/openai-service');
    (callOpenAI as any).mockResolvedValue(mockLLMResponse);

    // Mock JSON parse
    (safeJSONParse as any).mockReturnValue({
      course_title: 'Test Course',
      course_description: 'Generated description',
    });

    const result = await generateMetadata(job);

    expect(result).toBeDefined();
    expect(result.course_title).toBe('Test Course');
    expect(callOpenAI).toHaveBeenCalledWith(
      expect.objectContaining({
        model: 'OSS 20B', // Default model
      })
    );
  });

  it('should use style prompts when provided', async () => {
    const job = {
      course_title: 'Test Course',
      styles: { style_1: 'technical' },
      generation_mode: 'title-only' as const,
    };

    const { callOpenAI } = await import('@/services/llm/openai-service');
    (callOpenAI as any).mockResolvedValue('{}');
    (safeJSONParse as any).mockReturnValue({});

    await generateMetadata(job);

    expect(callOpenAI).toHaveBeenCalledWith(
      expect.objectContaining({
        prompt: expect.stringContaining('technical'),
      })
    );
  });

  it('should handle JSON repair on malformed LLM response', async () => {
    const job = {
      course_title: 'Test Course',
      styles: {},
      generation_mode: 'title-only' as const,
    };

    // Mock malformed JSON response
    const malformedJSON = '```json\n{"course_title": "Test",}\n```';

    const { callOpenAI } = await import('@/services/llm/openai-service');
    (callOpenAI as any).mockResolvedValue(malformedJSON);

    // Mock JSON repair success
    (safeJSONParse as any).mockReturnValue({ course_title: 'Test' });

    const result = await generateMetadata(job);

    expect(safeJSONParse).toHaveBeenCalledWith(malformedJSON);
    expect(result).toBeDefined();
  });
});
```

**T024 - Section Batch Generator Tests** - `packages/your-app/tests/unit/section-batch-generator.test.ts`:

```typescript
import { describe, it, expect, vi } from 'vitest';
import { generateSectionBatch } from '@/services/stage5/section-batch-generator';

vi.mock('@/services/llm/openai-service', () => ({
  callOpenAI: vi.fn(),
}));

describe('generateSectionBatch', () => {
  it('should generate section batch with SECTIONS_PER_BATCH=1', async () => {
    const metadata = {
      course_title: 'Test Course',
      sections: ['Section 1', 'Section 2'],
    };

    const batchIndex = 0;

    const { callOpenAI } = await import('@/services/llm/openai-service');
    (callOpenAI as any).mockResolvedValue(
      JSON.stringify({
        section_title: 'Section 1',
        lessons: [{ lesson_title: 'Lesson 1' }],
      })
    );

    const result = await generateSectionBatch(metadata, batchIndex);

    expect(result).toBeDefined();
    expect(result.section_title).toBe('Section 1');
    expect(callOpenAI).toHaveBeenCalledOnce();
  });

  it('should retry on validation failure (FR-019, max 3 retries)', async () => {
    const metadata = { course_title: 'Test', sections: ['Section 1'] };
    const batchIndex = 0;

    const { callOpenAI } = await import('@/services/llm/openai-service');

    // First 2 calls return invalid (no lessons), 3rd call succeeds
    (callOpenAI as any)
      .mockResolvedValueOnce(JSON.stringify({ section_title: 'Section 1', lessons: [] }))
      .mockResolvedValueOnce(JSON.stringify({ section_title: 'Section 1', lessons: [] }))
      .mockResolvedValueOnce(
        JSON.stringify({
          section_title: 'Section 1',
          lessons: [{ lesson_title: 'Lesson 1' }],
        })
      );

    const result = await generateSectionBatch(metadata, batchIndex);

    expect(callOpenAI).toHaveBeenCalledTimes(3);
    expect(result.lessons).toHaveLength(1);
  });

  it('should integrate style prompts into section generation', async () => {
    const metadata = {
      course_title: 'Test',
      sections: ['Section 1'],
      styles: { style_1: 'minimalist' },
    };

    const { callOpenAI } = await import('@/services/llm/openai-service');
    (callOpenAI as any).mockResolvedValue('{}');

    await generateSectionBatch(metadata, 0);

    expect(callOpenAI).toHaveBeenCalledWith(
      expect.objectContaining({
        prompt: expect.stringContaining('minimalist'),
      })
    );
  });
});
```

**For Utility Tests (T025, T028)**:

**T025 - JSON Repair & Field Name Fix Tests** - `packages/your-app/tests/unit/json-repair.test.ts`:

```typescript
import { describe, it, expect } from 'vitest';
import { safeJSONParse } from '@/services/stage5/json-repair';
import { fixFieldNames } from '@/services/stage5/field-name-fix';

describe('safeJSONParse - 4-level repair', () => {
  it('should parse valid JSON as-is', () => {
    const valid = '{"key": "value"}';
    const result = safeJSONParse(valid);

    expect(result).toEqual({ key: 'value' });
  });

  it('should extract JSON from markdown code blocks', () => {
    const markdown = '```json\n{"key": "value"}\n```';
    const result = safeJSONParse(markdown);

    expect(result).toEqual({ key: 'value' });
  });

  it('should balance missing closing braces', () => {
    const unbalanced = '{"key": "value", "nested": {"inner": "data"';
    const result = safeJSONParse(unbalanced);

    expect(result).toBeDefined();
    expect(result.nested.inner).toBe('data');
  });

  it('should remove trailing commas', () => {
    const trailingComma = '{"key": "value",}';
    const result = safeJSONParse(trailingComma);

    expect(result).toEqual({ key: 'value' });
  });

  it('should strip comments', () => {
    const withComments = `{
      "key": "value", // inline comment
      /* block comment */
      "key2": "value2"
    }`;
    const result = safeJSONParse(withComments);

    expect(result).toEqual({ key: 'value', key2: 'value2' });
  });

  it('should return null for irreparable JSON', () => {
    const invalid = 'not even close to JSON';
    const result = safeJSONParse(invalid);

    expect(result).toBeNull();
  });
});

describe('fixFieldNames - camelCase to snake_case (FR-019)', () => {
  it('should fix camelCase field names', () => {
    const input = { courseTitle: 'Test', targetAudience: 'Beginners' };
    const result = fixFieldNames(input);

    expect(result).toEqual({ course_title: 'Test', target_audience: 'Beginners' });
  });

  it('should recursively fix nested objects', () => {
    const input = {
      courseTitle: 'Test',
      metadata: {
        createdBy: 'User',
        lastModified: '2025-01-01',
      },
    };
    const result = fixFieldNames(input);

    expect(result.metadata.created_by).toBe('User');
    expect(result.metadata.last_modified).toBe('2025-01-01');
  });

  it('should handle arrays of objects', () => {
    const input = {
      sections: [
        { sectionTitle: 'Section 1' },
        { sectionTitle: 'Section 2' },
      ],
    };
    const result = fixFieldNames(input);

    expect(result.sections[0].section_title).toBe('Section 1');
    expect(result.sections[1].section_title).toBe('Section 2');
  });
});
```

**T028 - Validator & Sanitizer Tests** - `packages/your-app/tests/unit/validators.test.ts`:

```typescript
import { describe, it, expect } from 'vitest';
import { validateMinimumLessons } from '@/services/stage5/minimum-lessons-validator';
import { sanitizeCourseStructure } from '@/services/stage5/sanitize-course-structure';

describe('validateMinimumLessons (FR-015)', () => {
  it('should pass validation when all sections have lessons', () => {
    const course = {
      sections: [
        {
          section_title: 'Section 1',
          lessons: [{ lesson_title: 'Lesson 1' }],
        },
        {
          section_title: 'Section 2',
          lessons: [{ lesson_title: 'Lesson 2' }],
        },
      ],
    };

    const result = validateMinimumLessons(course);

    expect(result.valid).toBe(true);
    expect(result.errors).toHaveLength(0);
  });

  it('should fail validation when section has no lessons (FR-015 violation)', () => {
    const course = {
      sections: [
        {
          section_title: 'Section 1',
          lessons: [],
        },
      ],
    };

    const result = validateMinimumLessons(course);

    expect(result.valid).toBe(false);
    expect(result.errors).toHaveLength(1);
    expect(result.errors[0]).toContain('Section 1');
    expect(result.sectionsWithNoLessons).toContain('Section 1');
  });
});

describe('sanitizeCourseStructure - XSS protection', () => {
  it('should sanitize XSS attack vectors with DOMPurify', () => {
    const maliciousCourse = {
      course_title: '<script>alert("XSS")</script>Test Course',
      sections: [
        {
          section_title: '<img src=x onerror=alert(1)>Section 1',
          lessons: [
            {
              lesson_title: '<a href="javascript:alert(1)">Lesson 1</a>',
            },
          ],
        },
      ],
    };

    const sanitized = sanitizeCourseStructure(maliciousCourse);

    expect(sanitized.course_title).not.toContain('<script>');
    expect(sanitized.sections[0].section_title).not.toContain('<img');
    expect(sanitized.sections[0].lessons[0].lesson_title).not.toContain('javascript:');
  });

  it('should preserve safe text content', () => {
    const safeCourse = {
      course_title: 'Safe Course Title',
      sections: [
        {
          section_title: 'Safe Section',
          lessons: [{ lesson_title: 'Safe Lesson' }],
        },
      ],
    };

    const sanitized = sanitizeCourseStructure(safeCourse);

    expect(sanitized.course_title).toBe('Safe Course Title');
    expect(sanitized.sections[0].section_title).toBe('Safe Section');
  });

  it('should recursively sanitize nested structures', () => {
    const course = {
      sections: [
        {
          lessons: [
            { key_concepts: ['<script>XSS</script>Concept 1', 'Concept 2'] },
          ],
        },
      ],
    };

    const sanitized = sanitizeCourseStructure(course);

    expect(sanitized.sections[0].lessons[0].key_concepts[0]).not.toContain('<script>');
    expect(sanitized.sections[0].lessons[0].key_concepts[1]).toBe('Concept 2');
  });
});
```

**For Contract Tests (T041)**:

**T041 - Generation tRPC Contract Tests** - `packages/your-app/tests/contract/generation.tRPC.test.ts`:

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { appRouter } from '@/server/routers/_app';
import { createCallerFactory } from '@trpc/server';

// Mock tRPC context
const mockContext = {
  user: { id: 'user_123', email: 'test@example.com' },
  session: { id: 'session_123' },
};

const createCaller = createCallerFactory(appRouter);

describe('generation.tRPC contract tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should require authentication for generation.create', async () => {
    const caller = createCaller({ user: null }); // Unauthenticated

    await expect(
      caller.generation.create({
        course_title: 'Test',
        styles: {},
        generation_mode: 'title-only',
      })
    ).rejects.toThrow('UNAUTHORIZED');
  });

  it('should accept valid GenerationJob input', async () => {
    const caller = createCaller(mockContext);

    const input = {
      course_title: 'Test Course',
      styles: { style_1: 'minimalist' },
      generation_mode: 'title-only' as const,
    };

    const result = await caller.generation.create(input);

    expect(result).toBeDefined();
    expect(result.job_id).toBeDefined();
    expect(result.status).toBe('queued');
  });

  it('should reject invalid input schema', async () => {
    const caller = createCaller(mockContext);

    const invalidInput = {
      // Missing course_title
      styles: {},
      generation_mode: 'title-only',
    };

    await expect(caller.generation.create(invalidInput as any)).rejects.toThrow('Validation error');
  });

  it('should return correct error code for invalid generation_mode', async () => {
    const caller = createCaller(mockContext);

    const invalidInput = {
      course_title: 'Test',
      styles: {},
      generation_mode: 'invalid-mode' as any,
    };

    await expect(caller.generation.create(invalidInput)).rejects.toThrow();
  });

  it('should validate CourseStructure output schema', async () => {
    const caller = createCaller(mockContext);

    const result = await caller.generation.getResult({ job_id: 'job_123' });

    expect(result).toBeDefined();
    if (result.status === 'completed') {
      expect(result.course_structure).toBeDefined();
      expect(result.course_structure.course_title).toBeDefined();
      expect(result.course_structure.sections).toBeInstanceOf(Array);
    }
  });
});
```
