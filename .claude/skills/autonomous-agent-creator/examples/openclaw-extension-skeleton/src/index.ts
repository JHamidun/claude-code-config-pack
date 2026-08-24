import { Type } from '@sinclair/typebox';

/**
 * Plugin entry point. Called by OpenClaw to register the extension.
 */
export const definePluginEntry = () => ({
  id: 'my-extension',
  name: 'My Extension',
  version: '1.0.0',

  register(api: PluginAPI) {
    api.registerTool(myToolFactory, { names: ['my_tool'] });
  }
});

/** Plugin API interface (provided by OpenClaw runtime). */
interface PluginAPI {
  registerTool(factory: ToolFactory, opts: { names: string[] }): void;
  getConfig(): Record<string, unknown>;
}

type ToolFactory = (config: unknown) => {
  name: string;
  description: string;
  parameters: unknown;
  execute: (params: Record<string, unknown>) => Promise<unknown>;
};

/**
 * Tool factory: creates the my_tool instance with its schema and executor.
 */
function myToolFactory(_config: unknown) {
  return {
    name: 'my_tool',
    description:
      'Description of what this tool does. ' +
      'Call this when the user asks for X. ' +
      'Present the results as a formatted summary.',
    parameters: Type.Object({
      input: Type.String({ description: 'Input parameter' }),
      mode: Type.Optional(
        Type.Union([Type.Literal('fast'), Type.Literal('thorough')], {
          description: 'Processing mode (default: fast)'
        })
      )
    }),

    async execute(params: { input: string; mode?: string }) {
      const { input, mode = 'fast' } = params;

      try {
        // Your logic here
        const result = `Processed: ${input} (mode: ${mode})`;
        return { ok: true, result };
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : String(err);
        return { ok: false, error: message };
      }
    }
  };
}

export default definePluginEntry;
